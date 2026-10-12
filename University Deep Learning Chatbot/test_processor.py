"""Lightweight regression checks for BUSE Bot matching."""

from processor import chatbot_response, predict_class


def test_greeting():
    assert "BUSE" in chatbot_response("hello")


def test_fees():
    reply = chatbot_response("What is the fees structure")
    assert "fees" in reply.lower() or "US$" in reply


def test_apply():
    reply = chatbot_response("How to apply to BUSE")
    assert "apply" in reply.lower() or "application" in reply.lower()


def test_unknown():
    reply = chatbot_response("zzzz qwerty asdfgh unrelated gibberish")
    assert "not sure" in reply.lower() or "buse.ac.zw" in reply.lower()


def test_prediction_shape():
    preds = predict_class("Tell me about BUSE")
    assert preds
    assert "intent" in preds[0]


if __name__ == "__main__":
    test_greeting()
    test_fees()
    test_apply()
    test_unknown()
    test_prediction_shape()
    print("All processor checks passed.")
