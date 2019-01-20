
develop:
	docker run -it --rm \
		-v $(shell pwd):/app \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-e IAM_ROLE=arn:aws:iam::601394826940:role/admin \
		--workdir=/app \
		ktruckenmiller/ansible \
		sh

deploy:
	docker run -it --rm \
		-v $(shell pwd):/app \
		-v /var/run/docker.sock:/var/run/docker.sock \
		--workdir=/app \
		-e IAM_ROLE=arn:aws:iam::601394826940:role/admin \
		ktruckenmiller/ansible \
		ansible-playbook -i ansible_connection=localhost deploy.yml -vvv
