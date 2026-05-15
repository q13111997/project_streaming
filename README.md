## Câu lệnh SQL xem báo cáo realtime
** Top 10 `product_id` có lượt view cao nhất trong ngày hiện tại
```
make top-products
```
** Top 10 quốc gia có lượt view cao nhất trong ngày hiện tại (quốc gia được lấy dựa vào `domain`)
```
make top-countries
```
** Top 5 `referrer_url` có lượt view cao nhất trong ngày hiện tại
```
make top-referrers
```
** Với 1 quốc gia bất kỳ, lấy ra danh sách các `store_id` và lượt view tương ứng, sắp xếp theo lượt view giảm dần (Finland, Netherlands, Germany, Italy, Finland, United States, Germany...)
```
make store-views country=Finland
```
** Dữ liệu view phân bổ theo giờ của một `product_id` bất kỳ trong ngày (93016, 99558, 96620, 90940, 84771, 92003, 100350, 86911, 105898, 110577, 107330, 99316, 90393, 97871, 93240, 96490, 90933, 96280, 100349, 110543, 100348, 98154, 103538, 103479, 96677, 97112, 104172)
```
make hourly-product product=93016
```
** Dữ liệu view theo giờ của từng `browser`, `os`
```
make hourly-browser-os
```