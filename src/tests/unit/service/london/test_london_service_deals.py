import uuid

import pytest

from errors.error_services import DealAlreadyBought, DealDoubleBuying
from tests.test_data.models.mother_adverts import AdvertMother
from tests.test_data.models.mother_auth import UserMother
from tests.test_data.models.mother_deals_likes import DealMother


# ==============================================================================
# Тесты для метода create_deal (3 сценария)
# ==============================================================================
class TestCreateDeal:
    async def test_create_deal_when_already_in_user_deals(
        self, service_deal_london, mock_repo_user, mock_repo_advert, mock_repo_deal
    ):
        """Сценарий 1: сделка уже есть в сделках покупателя."""
        # Arrange
        user = UserMother.valid_user()
        advert = AdvertMother.valid_advert()
        mock_repo_user.does_exist.return_value = True
        mock_repo_advert.advert_exists.return_value = True
        mock_repo_deal.is_bought.return_value = False
        mock_repo_deal.is_in_deals.return_value = True

        # Act & Assert
        with pytest.raises(DealDoubleBuying):
            await service_deal_london.create_deal(user.id, advert.id)

    async def test_create_deal_when_not_yet_in_deals(
        self, service_deal_london, mock_repo_user, mock_repo_advert, mock_repo_deal
    ):
        """Сценарий 2: сделки еще нет — создаётся успешно."""
        # Arrange
        user = UserMother.valid_user()
        advert = AdvertMother.valid_advert()
        deal = DealMother.valid_deal_for(
            customer_id=user.id, advert_id=advert.id
        )
        mock_repo_user.does_exist.return_value = True
        mock_repo_advert.advert_exists.return_value = True
        mock_repo_deal.is_bought.return_value = False
        mock_repo_deal.is_in_deals.return_value = False
        mock_repo_deal.create_deal.return_value = deal

        # Act
        result = await service_deal_london.create_deal(user.id, advert.id)

        # Assert
        assert result == deal

    async def test_create_deal_when_already_bought_by_another_user(
        self, service_deal_london, mock_repo_user, mock_repo_advert, mock_repo_deal
    ):
        """Сценарий 3: сделка уже с другим пользователем."""
        # Arrange
        user_id, advert_id = uuid.uuid4(), uuid.uuid4()
        mock_repo_user.does_exist.return_value = True
        mock_repo_advert.advert_exists.return_value = True
        mock_repo_deal.is_bought.return_value = True

        # Act & Assert
        with pytest.raises(DealAlreadyBought):
            await service_deal_london.create_deal(user_id, advert_id)


# ==============================================================================
# Тесты для метода get_deals_by_user (2 сценария)
# ==============================================================================
class TestGetDealsByUser:
    async def test_get_deals_by_user_when_no_deals(
        self, service_deal_london, mock_repo_user, mock_repo_deal
    ):
        """Сценарий 1: у пользователя нет сделок."""
        # Arrange
        user = UserMother.valid_user()
        mock_repo_user.does_exist.return_value = True
        mock_repo_deal.get_deals_by_user.return_value = []

        # Act
        result = await service_deal_london.get_deals_by_user(user.id)

        # Assert
        assert result == []

    async def test_get_deals_by_user_when_has_deals(
        self, service_deal_london, mock_repo_user, mock_repo_deal
    ):
        """Сценарий 2: у пользователя есть сделки."""
        # Arrange
        user = UserMother.valid_user()
        adverts = AdvertMother.create_list(count=5)
        mock_repo_user.does_exist.return_value = True
        mock_repo_deal.get_deals_by_user.return_value = adverts

        # Act
        result = await service_deal_london.get_deals_by_user(user.id)

        # Assert
        assert result == adverts


# ==============================================================================
# Тесты для метода is_in_deals (2 сценария)
# ==============================================================================
class TestIsInDeals:
    async def test_is_in_deals_when_true(
        self, service_deal_london, mock_repo_user, mock_repo_advert, mock_repo_deal
    ):
        """Сценарий 1: в сделках."""
        # Arrange
        user = UserMother.valid_user()
        advert = AdvertMother.valid_advert()
        mock_repo_user.does_exist.return_value = True
        mock_repo_advert.advert_exists.return_value = True
        mock_repo_deal.is_in_deals.return_value = True

        # Act
        result = await service_deal_london.is_in_deals(user.id, advert.id)

        # Assert
        assert result is True

    async def test_is_in_deals_when_false(
        self, service_deal_london, mock_repo_user, mock_repo_advert, mock_repo_deal
    ):
        """Сценарий 2: не в сделках пользователя."""
        # Arrange
        user = UserMother.valid_user()
        advert = AdvertMother.valid_advert()
        mock_repo_user.does_exist.return_value = True
        mock_repo_advert.advert_exists.return_value = True
        mock_repo_deal.is_in_deals.return_value = False

        # Act
        result = await service_deal_london.is_in_deals(user.id, advert.id)

        # Assert
        assert result is False


# ==============================================================================
# Тесты для метода is_bought (2 сценария)
# ==============================================================================
class TestIsBought:
    async def test_is_bought_when_true(
        self, service_deal_london, mock_repo_advert, mock_repo_deal
    ):
        """Сценарий 1: куплено."""
        # Arrange
        advert = AdvertMother.valid_advert()
        mock_repo_advert.advert_exists.return_value = True
        mock_repo_deal.is_bought.return_value = True

        # Act
        result = await service_deal_london.is_bought(advert.id)

        # Assert
        assert result is True

    async def test_is_bought_when_false(
        self, service_deal_london, mock_repo_advert, mock_repo_deal
    ):
        """Сценарий 2: не куплено никем."""
        # Arrange
        advert = AdvertMother.valid_advert()
        mock_repo_advert.advert_exists.return_value = True
        mock_repo_deal.is_bought.return_value = False

        # Act
        result = await service_deal_london.is_bought(advert.id)

        # Assert
        assert result is False