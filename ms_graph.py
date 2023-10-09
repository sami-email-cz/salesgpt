from msgraph import GraphServiceClient, GraphRequestAdapter
from azure.identity.aio import ClientSecretCredential, OnBehalfOfCredential
# from azure.identity import UsernamePasswordCredential, ClientSecretCredential, OnBehalfOfCredential, EnvironmentCredential
from kiota_authentication_azure.azure_identity_authentication_provider import AzureIdentityAuthenticationProvider


class MSGraph:
    def __init__(self) -> None:
        tenant_id = 'ea1c68a2-710a-439e-8434-4928da637d51'
        client_id = '37447051-469a-4d5f-9f93-58c45dd555e9'
        client_secret = '6JG8Q~T8Ch_rGkKxzfrX0RVEiUM4psQn6vyhCcrC'

        # scopes = [
        #     'https://graph.microsoft.com/Calendars.ReadWrite',
        #     'https://graph.microsoft.com/Calendars.Read'
        #     ]
        
        # scopes = [
        #     'https://graph.microsoft.com/.default'
        #     ]

        scopes = [
            'Calendars.ReadWrite',
            'Calendars.Read'
            ]
        
        # self.credentials = EnvironmentCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret, authority_host='https://login.microsoftonline.com')
        self.credentials = ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret, authority='https://login.microsoftonline.com')
        # self.credentials = OnBehalfOfCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret, authority='https://login.microsoftonline.com', user_assertion='')
        # self.credentials = UsernamePasswordCredential(client_id=client_id, username='esterai@multima.cz', password='A63@8IzqawiB2iseBfN', authority=f'https://login.microsoftonline.com', tenant_id=tenant_id)
        auth_provider = AzureIdentityAuthenticationProvider(credentials=self.credentials, scopes=scopes)
        self.adapter = GraphRequestAdapter(auth_provider)
        self.client = GraphServiceClient(self.adapter)

        pass

    async def get_token(self, scope: str='.default'):
        # access_token =  self.credentials.get_token(f"https://graph.microsoft.com/{scope}")
        access_token =   await self.credentials.get_token(scope)
        # access_token =  await self.credentials.get_token("https://graph.microsoft.com/.default")
        return access_token.token