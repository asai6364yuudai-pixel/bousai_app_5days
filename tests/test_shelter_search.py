import unittest
from unittest.mock import patch

import app as application


class ShelterSearchTest(unittest.TestCase):
    def setUp(self):
        self.client = application.app.test_client()
        self.original_shelters = application.shelters
        self.original_instructions = application.instructions
        application.shelters = [
            {
                'id': 1, 'name': 'Beta', 'district': '東', 'address': '東京都東区1-1',
                'recommendation': '★★', 'crowding': '★★★', 'travel_time': '徒歩10分',
                'phone': '03-0000-0001',
            },
            {
                'id': 2, 'name': 'Alpha', 'district': '西', 'address': ' ',
                'recommendation': '★★★★★', 'crowding': '★',
            },
        ]
        application.instructions = [
            {'target': '住民', 'area': '本町', 'content': '本町のお知らせ', 'updated_at': '2026-09-02'},
            {'target': '住民', 'area': '新町,本町', 'content': '共通のお知らせ', 'updated_at': '2026-09-01'},
            {'target': '住民', 'area': '新町', 'content': '新町のお知らせ', 'updated_at': '2026-08-31'},
        ]

    def tearDown(self):
        application.shelters = self.original_shelters
        application.instructions = self.original_instructions

    def test_results_filter_sort_and_missing_fields(self):
        response = self.client.get('/search_results?district=%E6%9D%B1&sort=name')
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('検索結果', body)
        self.assertIn('Beta', body)
        self.assertIn('徒歩10分', body)
        self.assertIn('03-0000-0001', body)
        self.assertIn('data-address="東京都東区1-1"', body)
        self.assertNotIn('Alpha', body)
        self.assertIn('nominatim.openstreetmap.org/search', body)

    def test_addressless_shelter_has_no_map_or_address(self):
        body = self.client.get('/search_results?district=西').get_data(as_text=True)
        self.assertIn('Alpha', body)
        self.assertNotIn('class="shelter-map"', body)
        self.assertNotIn('住所', body)
        self.assertIn('未登録', body)

    def test_all_shelters_and_empty_state(self):
        self.assertEqual(self.client.get('/all_shelters').status_code, 200)
        body = self.client.get('/search_results?district=不存在').get_data(as_text=True)
        self.assertIn('該当する避難所が見つかりませんでした', body)

    def test_sorting_helper_and_district_preservation(self):
        results = application.filter_and_sort_shelters(application.shelters, sort='name')
        self.assertEqual([item['name'] for item in results], ['Alpha', 'Beta'])
        results = application.filter_and_sort_shelters(application.shelters, sort='recommendation')
        self.assertEqual(results[0]['name'], 'Alpha')
        results = application.filter_and_sort_shelters(application.shelters, sort='crowding')
        self.assertEqual(results[0]['name'], 'Alpha')
        results = application.filter_and_sort_shelters(application.shelters, district='東', sort='invalid')
        self.assertEqual([item['name'] for item in results], ['Beta'])
        body = self.client.get('/search_results?district=%E6%9D%B1&sort=name').get_data(as_text=True)
        self.assertIn('name"', body)
        self.assertIn('value="東"', body)

    def test_distance_sort_puts_addressless_shelters_last(self):
        shelters = [
            {'name': '遠い施設', 'address': '青森市内', 'latitude': 40.8300, 'longitude': 140.7500},
            {'name': '近い施設', 'address': '青森市内', 'latitude': 40.8246, 'longitude': 140.7433},
            {'name': '住所なし', 'address': ' ', 'latitude': 40.8245, 'longitude': 140.7432},
            {'name': '座標なし', 'address': '青森市内'},
        ]
        results = application.filter_and_sort_shelters(shelters, sort='distance')
        self.assertEqual(
            [shelter['name'] for shelter in results],
            ['近い施設', '遠い施設', '住所なし', '座標なし'],
        )
        self.assertIsNone(application.shelter_distance(shelters[2]))
        self.assertIsNone(application.shelter_distance(shelters[3]))

    def test_occupancy_rate_is_reflected_in_search_and_home(self):
        application.shelters[0].update({
            'accepted_count': '5', 'capacity': '10',
            'latitude': 35.0, 'longitude': 139.0,
        })
        prepared = application.prepare_shelters(application.shelters)
        self.assertEqual(prepared[0]['occupancy_display'], '50%')
        self.assertEqual(prepared[0]['congestion'], 'やや混雑')

        search_body = self.client.get('/search_results?district=%E6%9D%B1').get_data(as_text=True)
        home_body = self.client.get('/').get_data(as_text=True)
        self.assertIn('>50%</dd>', search_body)
        self.assertIn('occupancy_rate', home_body)
        self.assertIn('occupancy_display', home_body)

        application.shelters[1].update({'accepted_count': '9', 'capacity': '10'})
        results = application.filter_and_sort_shelters(application.shelters, sort='crowding')
        self.assertEqual(results[0]['name'], 'Beta')
        self.assertIn('0〜49%', home_body)
        self.assertIn('50〜79%', home_body)
        self.assertIn('80%以上', home_body)

    def test_home_notice_area_filter(self):
        all_body = self.client.get('/').get_data(as_text=True)
        filtered_body = self.client.get('/?area=%E6%9C%AC%E7%94%BA').get_data(as_text=True)
        invalid_body = self.client.get('/?area=invalid').get_data(as_text=True)
        self.assertIn('本町のお知らせ', all_body)
        self.assertIn('新町のお知らせ', all_body)
        self.assertIn('本町のお知らせ', filtered_body)
        self.assertIn('共通のお知らせ', filtered_body)
        self.assertNotIn('新町のお知らせ', filtered_body)
        self.assertIn('新町のお知らせ', invalid_body)
        self.assertIn('value="本町" selected', filtered_body)

    def test_home_emergency_rescue_notice(self):
        body = self.client.get('/').get_data(as_text=True)
        self.assertIn('命に関わる緊急の救助要請は、こちらにお電話ください', body)
        self.assertIn('href="tel:000-0000-0000"', body)
        self.assertIn('href="#emergency-rescue">救助要請</a>', body)

    def test_home_notice_status_colors(self):
        application.instructions.extend([
            {'target': '住民', 'area': '本町', 'content': '発令情報', 'status': '発令中', 'updated_at': '2026-09-03'},
            {'target': '住民', 'area': '本町', 'content': '解除情報', 'status': '解除', 'updated_at': '2026-09-04'},
        ])
        body = self.client.get('/').get_data(as_text=True)
        self.assertIn('status-issued', body)
        self.assertIn('status-released', body)

    def test_english_translation_covers_main_select_labels(self):
        with self.client.session_transaction() as session:
            session['language'] = 'en'
            session['logged_in'] = True
        search_body = self.client.get('/search_results').get_data(as_text=True)
        announcement_body = self.client.get('/announcement_register').get_data(as_text=True)
        instruction_body = self.client.get('/instruction_register').get_data(as_text=True)
        self.assertIn('<title>Search results - Disaster Prevention App</title>', search_body)
        self.assertIn('Least crowded', search_body)
        self.assertIn('Issued', announcement_body)
        self.assertIn('Released', announcement_body)
        self.assertIn('Disaster Management Office', instruction_body)
        self.assertIn('In progress', instruction_body)

    def test_announcement_registration_uses_announcement_statuses(self):
        with self.client.session_transaction() as session:
            session['logged_in'] = True
        response = self.client.get('/announcement_register')
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('<option value="発令">発令</option>', body)
        self.assertIn('<option value="解除">解除</option>', body)
        self.assertNotIn('未対応', body)
        self.assertNotIn('id="shelter"', body)

        with patch.object(application, 'save_instructions'):
            response = self.client.post('/announcement_register', data={
                'area': '本町', 'content': '警報', 'status': '解除', 'warning_type': '通常',
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(application.instructions[-1]['status'], '解除')
        self.assertNotIn('shelter', application.instructions[-1])

    def test_shelter_registration_saves_geocoded_coordinates(self):
        with self.client.session_transaction() as session:
            session['logged_in'] = True
        with patch.object(application, 'geocode_address', return_value={
            'latitude': 35.0001, 'longitude': 139.0002,
        }), patch.object(application, 'save_shelters'):
            response = self.client.post('/shelter_register', data={
                'name': 'テスト避難所', 'address': '東京都テスト区1-1',
                'accepted_count': '', 'capacity': '', 'phone': '', 'action': 'save',
            })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(application.shelters[-1]['latitude'], 35.0001)
        self.assertEqual(application.shelters[-1]['longitude'], 139.0002)

    def test_shelter_registration_removes_stale_coordinates_on_geocode_failure(self):
        with self.client.session_transaction() as session:
            session['logged_in'] = True
        application.shelters.append({
            'id': 99, 'name': '既存避難所', 'address': '旧住所',
            'latitude': 35.1, 'longitude': 139.1,
        })
        with patch.object(application, 'geocode_address', return_value=None), patch.object(application, 'save_shelters'):
            response = self.client.post('/shelter_register', data={
                'selected_id': '99', 'name': '既存避難所', 'address': '新住所',
                'accepted_count': '', 'capacity': '', 'phone': '', 'action': 'save',
            })
        self.assertEqual(response.status_code, 200)
        updated = next(item for item in application.shelters if item['id'] == 99)
        self.assertNotIn('latitude', updated)
        self.assertNotIn('longitude', updated)


if __name__ == '__main__':
    unittest.main()
