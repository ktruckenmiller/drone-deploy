
develop:
	docker run -it --rm \
		-v $(shell pwd):/app \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-e IAM_ROLE \
		--workdir=/app \
		ktruckenmiller/ansible \
		sh

deploy:
	docker run -it --rm \
		-v $(shell pwd):/app \
		-v /var/run/docker.sock:/var/run/docker.sock \
		--workdir=/app \
		-e IAM_ROLE \
		ktruckenmiller/ansible \
		ansible-playbook -i ansible_connection=localhost deploy.yml -vvv

# local-agent:
