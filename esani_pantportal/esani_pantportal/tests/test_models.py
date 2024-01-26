# SPDX-FileCopyrightText: 2023 Magenta ApS <info@magenta.dk>
#
# SPDX-License-Identifier: MPL-2.0
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import SimpleTestCase, TestCase

from esani_pantportal.models import (
    BranchUser,
    Company,
    CompanyBranch,
    CompanyUser,
    DepositPayout,
    DepositPayoutItem,
    EsaniUser,
    Kiosk,
    KioskUser,
    Product,
    QRCodeGenerator,
    QRCodeInterval,
    validate_barcode_length,
    validate_digit,
)


class ValidationTest(SimpleTestCase):
    def test_barcode_length(self):
        self.assertRaises(
            ValidationError,
            validate_barcode_length,
            "1234",
        )

    def test_digit(self):
        self.assertRaises(
            ValidationError,
            validate_digit,
            "abc",
        )


class QRCodeGeneratorTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        QRCodeGenerator.objects.create(name="Små sække", prefix=0)
        QRCodeGenerator.objects.create(name="Store sække", prefix=1)

    def test_generate_qr(self):
        små_generator = QRCodeGenerator.objects.get(prefix=0)
        store_generator = QRCodeGenerator.objects.get(prefix=1)
        id_length = settings.QR_ID_LENGTH + 1
        små_qrs_1 = små_generator.generate_qr_codes(10)
        små_qrs_2 = små_generator.generate_qr_codes(5, salt="salt")  # noqa

        store_generator.generate_qr_codes(5)

        sm_qr_first = små_qrs_1[0]
        sm_qr_last = små_qrs_2[-1]

        self.assertEqual(len(små_generator.check_qr_code(sm_qr_first)), id_length)
        self.assertEqual(len(små_generator.check_qr_code(sm_qr_last)), id_length)
        self.assertEqual(store_generator.check_qr_code(sm_qr_first), None)

        sm_qr_wrong = sm_qr_first[:-1] + "x"  # 'x' can't be part of a hex digest
        self.assertEqual(store_generator.check_qr_code(sm_qr_wrong), None)

    def test_qr_not_generated_by_us(self):
        generator = QRCodeGenerator.objects.get(prefix=0)

        # The `v` is not in our QR spec.
        ok = generator.check_qr_code("http://pant.gl?QR=000v0000004cd04636")
        self.assertEqual(ok, None)

    def test_wrong_control_digits(self):
        generator = QRCodeGenerator.objects.get(prefix=0)

        # The control digits are wrong because no QR codes have been generated
        ok = generator.check_qr_code("http://pant.gl?QR=00000000004cd04636")
        self.assertEqual(ok, None)

    def test_str(self):
        generator = QRCodeGenerator.objects.get(prefix=0)
        generator_str = f"{generator.name} - {generator.prefix} ({generator.count})"
        self.assertEqual(str(generator), generator_str)

    def test_qr_code_exists(self):
        ok = QRCodeGenerator.qr_code_exists("00000000004cd04636")
        self.assertEqual(ok, False)


class QRCodeIntervalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.generator = QRCodeGenerator.objects.create(name="Små sække", prefix=0)

    def test_str(self):
        self.generator.generate_qr_codes(1, salt="foo")
        qr_interval = QRCodeInterval.objects.get(salt="foo")
        self.assertIn("foo", str(qr_interval))


class KioskTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.kiosk = Kiosk.objects.create(name="my kiosk", cvr=11221122)

    def test_str(self):
        self.assertEqual(str(self.kiosk), "my kiosk - cvr: 11221122")

    def test_get_branch(self):
        self.assertEqual(self.kiosk.get_branch(), self.kiosk)

    def test_get_company(self):
        self.assertEqual(self.kiosk.get_company(), None)


class CompanyTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(name="my company", cvr=11221122)

    def test_get_branch(self):
        self.assertEqual(self.company.get_branch(), None)

    def test_get_company(self):
        self.assertEqual(self.company.get_company(), self.company)


class CompanyBranchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.company = Company.objects.create(name="my company", cvr=11221122)
        cls.branch = CompanyBranch.objects.create(name="my branch", company=cls.company)

    def test_get_branch(self):
        self.assertEqual(self.branch.get_branch(), self.branch)

    def test_get_company(self):
        self.assertEqual(self.branch.get_company(), self.company)


class DepositPayoutTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.deposit_payout = DepositPayout.objects.create(
            source_type=DepositPayout.SOURCE_TYPE_CSV,
            source_identifier="hello",
            from_date="20230101",
            to_date="20240101",
            item_count=127,
        )

    def test_str(self):
        self.assertNotEqual(str(self.deposit_payout), "Hello World!")


class DepositPayoutItemTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        deposit_payout = DepositPayout.objects.create(
            source_type=DepositPayout.SOURCE_TYPE_CSV,
            source_identifier="hello",
            from_date="20230101",
            to_date="20240101",
            item_count=127,
        )
        cls.deposit_payout_item = DepositPayoutItem.objects.create(
            deposit_payout=deposit_payout,
            location_id=1,
            rvm_serial=2,
            date="20230101",
            barcode="123",
            count=27,
        )

    def test_str(self):
        self.assertNotEqual(str(self.deposit_payout_item), "Hello world!")


class UserTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.facebook = Company.objects.create(
            name="facebook",
            cvr=12312345,
            address="foo",
            postal_code="123",
            city="test city",
            phone="+4544457845",
        )

        cls.facebook_branch = CompanyBranch.objects.create(
            company=cls.facebook,
            name="facebook_branch",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
        )

        cls.kiosk = Kiosk.objects.create(
            name="kiosk",
            address="food",
            postal_code="12311",
            city="test town",
            phone="+4542457845",
            location_id=2,
            cvr=11221122,
        )

        cls.facebook_admin = CompanyUser.objects.create_user(
            username="facebook_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            company=cls.facebook,
        )

        cls.facebook_branch_admin = BranchUser.objects.create_user(
            username="facebook_branch_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.facebook_branch,
        )

        cls.kiosk_admin = KioskUser.objects.create_user(
            username="kiosk_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
            branch=cls.kiosk,
        )

        cls.esani_admin = EsaniUser.objects.create_user(
            username="esani_admin",
            password="12345",
            email="test@test.com",
            phone="+4542457845",
        )

    def test_branch_property(self):
        self.assertEqual(self.facebook_branch_admin.branch, self.facebook_branch)
        self.assertEqual(self.kiosk_admin.branch, self.kiosk)

    def test_company_property(self):
        self.assertEqual(self.facebook_branch_admin.company, self.facebook)
        self.assertEqual(self.facebook_admin.company, self.facebook)

    def test_user_profile_property(self):
        self.assertEqual(
            str(self.esani_admin.user_profile),
            "esani_admin - ESANI User",
        )
        self.assertEqual(
            str(self.kiosk_admin.user_profile),
            "kiosk_admin - Kiosk User",
        )
        self.assertEqual(
            str(self.facebook_admin.user_profile),
            "facebook_admin - Company User",
        )
        self.assertEqual(
            str(self.facebook_branch_admin.user_profile),
            "facebook_branch_admin - Branch User",
        )


class ProductTest(TestCase):
    def test_create_product(self):
        product1 = Product.objects.create(
            product_name="prod1",
            barcode="0010",
            refund_value=3,
            approved=False,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

        self.assertEqual(product1.product_name, "prod1")

    def test_create_product_existing_barcode(self):
        product1 = Product(
            product_name="prod1",
            barcode="0011",
            refund_value=3,
            approved=False,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

        product2 = Product(
            product_name="prod2",
            barcode="0011",
            refund_value=3,
            approved=False,
            material="A",
            height=100,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

        product1.save()

        with self.assertRaisesRegexp(IntegrityError, ".*duplicate key value.*"):
            product2.save()

    def test_create_product_invalid_dimensions(self):
        product = Product(
            product_name="prod2",
            barcode="0011",
            refund_value=3,
            approved=False,
            material="A",
            height=10,
            diameter=60,
            weight=20,
            capacity=500,
            shape="F",
        )

        with self.assertRaisesRegexp(IntegrityError, "height_constraints"):
            product.save()
