from django.utils.crypto import salted_hmac

class SimpleTokenGenerator:
    def make_token(self, user):
        # Siempre usa user.pk → funciona aunque el PK no se llame "id"
        key = f"{user.pk}{user.numero_documento}{user.contrasena}"
        return salted_hmac("simple-token", key).hexdigest()

    def check_token(self, user, token):
        return self.make_token(user) == token

token_generator = SimpleTokenGenerator()

