from rizana.api.models.shared import DBModel


class PaymentIntentResponse(DBModel):
    """
    Represents the response from Stripe after creating a payment intent.

    Attributes:
        client_secret (str): The client secret used to complete the payment on the frontend.
        payment_intent_id (str): The unique identifier of the payment intent in Stripe.
    """

    client_secret: str
    payment_intent_id: str
