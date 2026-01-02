"""Tests for agent type definitions."""

from src.agent.types import AgentDeps, DishCredentials, GoogleCalendarTokens

SAMPLE_EXPIRY_TIMESTAMP = 1735689600000


class TestDishCredentials:
    """Tests for the DishCredentials dataclass."""

    def test_creation_with_all_fields(self) -> None:
        """Test creating DishCredentials with all required fields."""
        creds = DishCredentials(
            cookie="session-cookie",
            team_id="team-abc",
            member_id="member-xyz",
        )

        assert creds.cookie == "session-cookie"
        assert creds.team_id == "team-abc"
        assert creds.member_id == "member-xyz"

    def test_empty_string_values(self) -> None:
        """Test creating DishCredentials with empty string values."""
        creds = DishCredentials(cookie="", team_id="", member_id="")

        assert creds.cookie == ""
        assert creds.team_id == ""
        assert creds.member_id == ""

    def test_equality(self) -> None:
        """Test that two DishCredentials with same values are equal."""
        creds1 = DishCredentials(cookie="c", team_id="t", member_id="m")
        creds2 = DishCredentials(cookie="c", team_id="t", member_id="m")

        assert creds1 == creds2

    def test_inequality(self) -> None:
        """Test that two DishCredentials with different values are not equal."""
        creds1 = DishCredentials(cookie="c1", team_id="t", member_id="m")
        creds2 = DishCredentials(cookie="c2", team_id="t", member_id="m")

        assert creds1 != creds2


class TestGoogleCalendarTokens:
    """Tests for the GoogleCalendarTokens dataclass."""

    def test_creation_with_all_fields(self) -> None:
        """Test creating GoogleCalendarTokens with all required fields."""
        tokens = GoogleCalendarTokens(
            access_token="access-123",
            refresh_token="refresh-456",
            expiry_date=SAMPLE_EXPIRY_TIMESTAMP,
        )

        assert tokens.access_token == "access-123"
        assert tokens.refresh_token == "refresh-456"
        assert tokens.expiry_date == SAMPLE_EXPIRY_TIMESTAMP

    def test_expiry_date_as_zero(self) -> None:
        """Test creating tokens with zero expiry date."""
        tokens = GoogleCalendarTokens(
            access_token="access",
            refresh_token="refresh",
            expiry_date=0,
        )

        assert tokens.expiry_date == 0

    def test_equality(self) -> None:
        """Test that two GoogleCalendarTokens with same values are equal."""
        tokens1 = GoogleCalendarTokens(access_token="a", refresh_token="r", expiry_date=100)
        tokens2 = GoogleCalendarTokens(access_token="a", refresh_token="r", expiry_date=100)

        assert tokens1 == tokens2

    def test_inequality_different_expiry(self) -> None:
        """Test that tokens with different expiry dates are not equal."""
        tokens1 = GoogleCalendarTokens(access_token="a", refresh_token="r", expiry_date=100)
        tokens2 = GoogleCalendarTokens(access_token="a", refresh_token="r", expiry_date=200)

        assert tokens1 != tokens2


class TestAgentDeps:
    """Tests for the AgentDeps dataclass."""

    def test_default_values(self) -> None:
        """Test AgentDeps is created with None defaults."""
        deps = AgentDeps()

        assert deps.dish is None
        assert deps.google_calendar is None

    def test_with_dish_credentials_only(self, dish_credentials: DishCredentials) -> None:
        """Test AgentDeps with only DiSH credentials."""
        deps = AgentDeps(dish=dish_credentials)

        assert deps.dish == dish_credentials
        assert deps.google_calendar is None

    def test_with_google_calendar_only(self, google_calendar_tokens: GoogleCalendarTokens) -> None:
        """Test AgentDeps with only Google Calendar tokens."""
        deps = AgentDeps(google_calendar=google_calendar_tokens)

        assert deps.dish is None
        assert deps.google_calendar == google_calendar_tokens

    def test_with_all_credentials(
        self,
        dish_credentials: DishCredentials,
        google_calendar_tokens: GoogleCalendarTokens,
    ) -> None:
        """Test AgentDeps with all credentials populated."""
        deps = AgentDeps(
            dish=dish_credentials,
            google_calendar=google_calendar_tokens,
        )

        assert deps.dish == dish_credentials
        assert deps.google_calendar == google_calendar_tokens

    def test_equality(self, agent_deps: AgentDeps) -> None:
        """Test that two AgentDeps with same values are equal."""
        deps1 = agent_deps
        deps2 = AgentDeps(
            dish=DishCredentials(
                cookie="test-cookie-value",
                team_id="test-team-123",
                member_id="test-member-456",
            ),
            google_calendar=GoogleCalendarTokens(
                access_token="test-access-token",
                refresh_token="test-refresh-token",
                expiry_date=SAMPLE_EXPIRY_TIMESTAMP,
            ),
        )

        assert deps1 == deps2
