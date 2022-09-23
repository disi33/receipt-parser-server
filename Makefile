.PHONY serve:

generate_cert:
	bash util/generate_certificate.sh

generate_token:
	bash util/generate_token.sh

serve:
	bash util/generate_certificate.sh
	bash util/generate_token.sh
	python src/receipt_server.py

.PHONY: docker-build
docker-build:
	docker build -t disi33/receipt-parser-server .

.PHONY: docker-build-test
docker-build-test:
	docker build -t disi33/receipt-parser-server-test .

.PHONY: docker-push
docker-push:
	docker push disi33/receipt-parser-server

.PHONY: docker-push-test
docker-push-test:
	docker push disi33/receipt-parser-server-test

.PHONY: docker-run
docker-run:
	bash util/launcher.sh
