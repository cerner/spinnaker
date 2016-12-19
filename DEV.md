### Install minikube

	brew cask install minikube
  brew install kubernetes-cli
	minikube start

Note: It looks like there may be a problem with the latest (0.14.0) minikube and spinnaker. The most recent version that works seems to be 0.12.12. Prior to installing, run the following:

  cd /usr/local/Homebrew/Library/Taps/caskroom/homebrew-cask
  git checkout dc03239


### Clone Spinnaker

	git clone git@github.cerner.com:norbert/spinnaker.git
  cd spinnaker
  git checkout norbert

* Copy minikube keys to ./config/kube

		cp ~/.minikube/{*.crt,*.pem,*.key} config/kube

* Get minikube config

		kubectl config view > ./config/kube/config

* Replace `~/.minikube` in config file with `/opt/spinnaker/config/kube`. For example:

	    apiVersion: v1
		clusters:
		- cluster:
		    certificate-authority: /opt/spinnaker/config/kube/ca.crt
		    server: https://192.168.99.100:8443
		  name: minikube
		contexts:
		- context:
		    cluster: minikube
		    user: minikube
		  name: minikube
		current-context: minikube
		kind: Config
		preferences:
		  colors: true
		users:
		- name: minikube
		  user:
		    client-certificate: /opt/spinnaker/config/kube/apiserver.crt
		    client-key: /opt/spinnaker/config/kube/apiserver.key

### Create spinnaker-local.yml

	providers:
		kubernetes:
		    # For more information on configuring Kubernetes clusters (kubernetes), see
		    # http://www.spinnaker.io/v1.0/docs/target-deployment-setup#section-kubernetes-cluster-setup

		    # NOTE: enabling kubernetes also requires enabling dockerRegistry.
		    enabled: true
		    primaryCredentials:
		      # These credentials use authentication information at ~/.kube/config
		      # by default.
		      name: minikube
		      dockerRegistryAccount: ${providers.dockerRegistry.primaryCredentials.name}

		  dockerRegistry:
		    # For more information on configuring Docker registries, see
		    # http://www.spinnaker.io/v1.0/docs/target-deployment-configuration#section-docker-registry

		    # NOTE: Enabling dockerRegistry is independent of other providers.
		    # However, for convienience, we tie docker and kubernetes together
		    # since kubernetes (and only kubernetes) depends on this docker provider
		    # configuration.
		    enabled: true

		    primaryCredentials:
		      name: my-docker-registry
		      address: ${SPINNAKER_DOCKER_REGISTRY:https://index.docker.io/}
		      username: ${SPINNAKER_DOCKER_USERNAME}
		      # A path to a plain text file containing the user's password
		      passwordFile: /opt/spinnaker/config/docker/passwd


### Create clouddriver-local.yml

		dockerRegistry:
		  enabled: ${providers.dockerRegistry.enabled:false}
		  accounts:
		    - name: ${providers.dockerRegistry.primaryCredentials.name}
		      address: ${providers.dockerRegistry.primaryCredentials.address}
		      username: ${providers.dockerRegistry.primaryCredentials.username:}
		      passwordFile: ${providers.dockerRegistry.primaryCredentials.passwordFile}
		      repositories:
		         - library/nginx
		         - willgorman/graphite
		         - willgorman/nginx-test

### Update compose.env

Add:

	SPINNAKER_DOCKER_USERNAME=<your hub.docker.com username>

### Add docker credentials

Create `config/docker/passwd` text file with your hub.docker.com password (and NO trailing newline or whitespace)

### Launch!

Probably want to give your Docker VM at least 8GB RAM.

	cd experimental/docker-compose
	docker-compose up -d

Now wait.  A while.

* View Kubernetes dashboard

		minikube dashboard

* Open localhost:9000 for Spinnaker UI
