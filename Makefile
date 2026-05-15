.PHONY: up down setup-db run bash

up:
	cd environment && docker compose up -d

down:
	cd environment && docker compose down 

setup-hdfs:
	docker exec -it namenode hdfs dfs -mkdir -p /tmp/checkpoints
	docker exec -it namenode hdfs dfs -chmod -R 777 /tmp

run:
	docker exec -it namenode hdfs dfsadmin -safemode leave || true
	docker exec -it spark-client bash -c "cd /workspace && PYTHONPATH=/workspace python src/scripts/database_setup.py"
	docker exec -it spark-client bash -c "cd /workspace && PYTHONPATH=/workspace python -u src/main.py"

remove-checkpoint:
	docker exec -it namenode hdfs dfs -rm -r -f -skipTrash "/tmp/checkpoint/log_views/*"

bash:
	docker exec -it spark-client /bin/bash

reset-offset:
	docker exec -it namenode hdfs dfs -rm -r -f /tmp/checkpoint/log_views || true
	docker exec -it spark-client touch /tmp/reset_kafka_marker

rerun:
	docker exec -it stream_postgres psql -U admin -d postgres -c "\
		DROP TABLE IF EXISTS fact_logs, dim_product, dim_store, dim_location, dim_device, dim_referrer, dim_date, dim_time CASCADE;"
	docker exec -it namenode hdfs dfs -rm -r -f -skipTrash "/tmp/checkpoint/log_views/*"
	docker exec -it spark-client touch /tmp/reset_kafka_marker
	$(MAKE) run

# http://localhost:9870/dfshealth.html#tab-overview
# http://localhost:8088/cluster
# http://localhost:4040/StreamingQuery/
# http://localhost:3000/dashboard/2-real-time-analytics-of-glamira-users

# =========================
# ANALYTICS QUERIES
# =========================

PSQL=docker exec -it stream_postgres \
	psql -U admin -d postgres -P pager=off -c

top-products:
	@$(PSQL) " \
	SELECT \
	    fl.product_id, \
	    COUNT(*) AS total_views \
	FROM fact_logs fl \
	JOIN dim_date dd \
	    ON fl.date_key = dd.date_key \
	WHERE dd.full_date = CURRENT_DATE \
	GROUP BY fl.product_id \
	ORDER BY total_views DESC \
	LIMIT 10; \
	"

top-countries:
	@$(PSQL) "\
	SELECT \
	    ds.domain, \
	    COUNT(*) AS total_views \
	FROM fact_logs fl \
	JOIN dim_date dd \
	    ON fl.date_key = dd.date_key \
	JOIN dim_store ds \
	    ON fl.store_id = ds.store_id \
	WHERE dd.full_date = CURRENT_DATE \
	GROUP BY ds.domain \
	ORDER BY total_views DESC \
	LIMIT 10;"

top-referrers:
	@$(PSQL) "\
	SELECT \
	    dr.referrer_domain, \
	    COUNT(*) AS total_views \
	FROM fact_logs fl \
	JOIN dim_date dd \
	    ON fl.date_key = dd.date_key \
	JOIN dim_referrer dr \
	    ON fl.referrer_key = dr.referrer_key \
	WHERE dd.full_date = CURRENT_DATE \
	GROUP BY dr.referrer_domain \
	ORDER BY total_views DESC \
	LIMIT 5;"

store-views:
	@$(PSQL) "\
	SELECT \
	    fl.store_id, \
	    ds.store_name, \
	    COUNT(*) AS total_views \
	FROM fact_logs fl \
	JOIN dim_location dl \
	    ON fl.location_key = dl.location_key \
	JOIN dim_store ds \
	    ON fl.store_id = ds.store_id \
	WHERE dl.country_name = '$(country)' \
	GROUP BY \
	    fl.store_id, \
	    ds.store_name \
	ORDER BY total_views DESC;"

hourly-product:
	@$(PSQL) "\
	SELECT \
	    dt.hour, \
	    COUNT(*) AS total_views \
	FROM fact_logs fl \
	JOIN dim_date dd \
	    ON fl.date_key = dd.date_key \
	JOIN dim_time dt \
	    ON fl.time_key = dt.time_key \
	WHERE dd.full_date = CURRENT_DATE \
	  AND fl.product_id = '$(product)' \
	GROUP BY dt.hour \
	ORDER BY dt.hour;"

hourly-browser-os:
	@$(PSQL) "\
	SELECT \
	    dt.hour, \
	    ddv.browser, \
	    ddv.os, \
	    COUNT(*) AS total_views \
	FROM fact_logs fl \
	JOIN dim_date dd \
	    ON fl.date_key = dd.date_key \
	JOIN dim_time dt \
	    ON fl.time_key = dt.time_key \
	JOIN dim_device ddv \
	    ON fl.device_key = ddv.device_key \
	WHERE dd.full_date = CURRENT_DATE \
	GROUP BY \
	    dt.hour, \
	    ddv.browser, \
	    ddv.os \
	ORDER BY \
	    dt.hour, \
	    total_views DESC;"