from xmtp_agent.errors import AgentError, AgentStreamingError


def test_agent_errors() -> None:
    assert isinstance(AgentError('msg'), Exception)
    assert isinstance(AgentStreamingError('msg'), AgentError)
