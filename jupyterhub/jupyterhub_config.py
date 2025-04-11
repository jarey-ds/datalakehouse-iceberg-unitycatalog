from dockerspawner import DockerSpawner
from oauthenticator.generic import GenericOAuthenticator
from jupyterhub.handlers import BaseHandler
import os


class CustomOauth2Authenticator(GenericOAuthenticator):
    async def authenticate(self, handler, data=None):
        user_info = await super().authenticate(handler, data)
        # Logueos de datos para comprobación de la gestión de datos de usuario.
        self.log.info("User info received: %s", user_info)
        return user_info


c = get_config()

c.JupyterHub.authenticator_class = CustomOauth2Authenticator
c.JupyterHub.spawner_class = DockerSpawner  # Creador de los notebooks.

c.CustomOauth2Authenticator.client_id = "jupyterhub-client"
c.CustomOauth2Authenticator.client_secret = "supersecret"
c.CustomOauth2Authenticator.oauth_callback_url = "http://localhost:8000/hub/oauth_callback"
c.CustomOauth2Authenticator.scope = ['openid', 'email', 'profile']
c.Authenticator.allowed_users = {'testuser'}
c.Authenticator.admin_users = {'testuser'}
c.CustomOauth2Authenticator.userdata_method = 'GET'
c.CustomOauth2Authenticator.username_claim = 'preferred_username'

c.CustomOauth2Authenticator.authorize_url = 'http://keycloak:8080/realms/jupyterhub/protocol/openid-connect/auth'
c.CustomOauth2Authenticator.token_url = 'http://keycloak:8080/realms/jupyterhub/protocol/openid-connect/token'
c.CustomOauth2Authenticator.userdata_url = 'http://keycloak:8080/realms/jupyterhub/protocol/openid-connect/userinfo'

c.Authenticator.auto_login = True
c.Authenticator.enable_auth_state = True

# DockerSpawner config
notebook_image = os.environ.get('DOCKER_NOTEBOOK_IMAGE', 'jupyterhub/jupyterhub:5')
c.DockerSpawner.image = notebook_image
#c.DockerSpawner.remove = True
c.DockerSpawner.network_name = 'jupyter-network'  # nombre de la red en el fichero compose.
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.debug = True


# DockerSpawner setup
c.DockerSpawner.extra_create_kwargs = {
    #'user': '{username}',  # Gestión del usario cuando arranca el contenedor mediante dockerspawner
    #'user': '1000:1000',
    'user': 'root',
    'environment': {
        'USER': '{username}',
        'HOME': '/home/{username}',
    }
}

c.Spawner.environment = {
    'HUB_IP': 'jupyterhub',  # Nombre del servicio de jupyterhub en el fichero compose.
    'JUPYTERHUB_API_URL': 'http://jupyterhub:8081/hub/api'
}

c.DockerSpawner.volumes = {
    'jupyterhub-user-{username}': '/home/{username}'
}

c.DockerSpawner.cmd = [
    "sh", "-c", "useradd -m $USER && /usr/local/bin/start-notebook.sh"
]


# Personalización del processo de generación del notebook.
async def add_oauth_token_to_environment(spawner):
    auth_state = await spawner.user.get_auth_state()
    token = auth_state.get("access_token", "no_tiene_valor")
    spawner.environment["OAUTH_ACCESS_TOKEN"] = token


# Hook a la función para gestionar el evento pre_spawn
c.DockerSpawner.pre_spawn_hook = add_oauth_token_to_environment

c.DockerSpawner.start_timeout = 300  # Increase the timeout to 300 seconds

# IP del Hub en al red de Docker
c.JupyterHub.hub_ip = '0.0.0.0'