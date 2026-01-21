def test_import_smoke() -> None:
    from xmtp import Client, ClientOptions
    from xmtp_agent import Agent
    from xmtp_content_type_markdown import MarkdownCodec
    from xmtp_content_type_reaction import ReactionCodec
    from xmtp_content_type_text import ContentTypeText, TextCodec

    assert ClientOptions
    assert Client
    assert Agent
    assert ContentTypeText
    TextCodec()
    MarkdownCodec()
    ReactionCodec()
