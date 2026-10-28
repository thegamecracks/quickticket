"""
2026-10-05
Fake data for use in testing. AI-generated.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from quickticket.models import (
    Address,
    Currency,
    Event,
    Money,
    Organization,
    OrganizationMember,
    Ticket,
    User,
    Venue,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(kw_only=True, repr=False)
class Dataset:
    users: Sequence[User]
    addresses: Sequence[Address]
    organizations: Sequence[Organization]
    organization_members: Sequence[OrganizationMember]
    venues: Sequence[Venue]
    events: Sequence[Event]
    tickets: Sequence[Ticket]

    def add_all(self, session: AsyncSession) -> None:
        session.add_all(self.users)
        session.add_all(self.addresses)
        session.add_all(self.organizations)
        session.add_all(self.organization_members)
        session.add_all(self.venues)
        session.add_all(self.events)
        session.add_all(self.tickets)


def create_test_models() -> Dataset:
    users = [
        User(
            id=UUID("eec50538-0edc-469b-b441-01b95b2f86c1"),
            display_name="James Smith",
            first_name="James",
            last_name="Smith",
            email="james.smith0@example.com",
        ),
        User(
            id=UUID("cd1e919c-78ac-4222-96c1-6bea98f57281"),
            display_name="Maria Johnson",
            first_name="Maria",
            last_name="Johnson",
            email="maria.johnson1@example.com",
        ),
        User(
            id=UUID("63363a5a-f35b-4b76-84b0-aa354843e426"),
            display_name="Liam Williams",
            first_name="Liam",
            last_name="Williams",
            email="liam.williams2@example.com",
        ),
        User(
            id=UUID("75e4418a-1216-4988-afd0-74db0f4d121f"),
            display_name="Sophie Brown",
            first_name="Sophie",
            last_name="Brown",
            email="sophie.brown3@example.com",
        ),
        User(
            id=UUID("bb355aea-9041-4fc3-b0ff-cd55a8fb6a46"),
            display_name="Noah Jones",
            first_name="Noah",
            last_name="Jones",
            email="noah.jones4@example.com",
        ),
        User(
            id=UUID("521df1bc-8a74-40c7-a768-c41dcf49e02b"),
            display_name="Ava Garcia",
            first_name="Ava",
            last_name="Garcia",
            email="ava.garcia5@example.com",
        ),
        User(
            id=UUID("e9706931-6932-4a7c-9a48-0c81728b4ee0"),
            display_name="Ethan Miller",
            first_name="Ethan",
            last_name="Miller",
            email="ethan.miller6@example.com",
        ),
        User(
            id=UUID("3f7b69d9-8908-4350-b7f4-eb3bcb303455"),
            display_name="Chloe Davis",
            first_name="Chloe",
            last_name="Davis",
            email="chloe.davis7@example.com",
        ),
        User(
            id=UUID("7094965f-be3d-49db-8a3d-c8e1bc8b3f99"),
            display_name="Lucas Rodriguez",
            first_name="Lucas",
            last_name="Rodriguez",
            email="lucas.rodriguez8@example.com",
        ),
        User(
            id=UUID("6f04f89b-e24a-43ac-8bb4-4b692db482ba"),
            display_name="Emma Martinez",
            first_name="Emma",
            last_name="Martinez",
            email="emma.martinez9@example.com",
        ),
        User(
            id=UUID("94f35ca2-5e50-4cde-b814-37c8169c0614"),
            display_name="Oliver Hernandez",
            first_name="Oliver",
            last_name="Hernandez",
            email="oliver.hernandez10@example.com",
        ),
        User(
            id=UUID("0daec970-3840-4aad-b2fb-05c1e4fa635d"),
            display_name="Julia Lopez",
            first_name="Julia",
            last_name="Lopez",
            email="julia.lopez11@example.com",
        ),
        User(
            id=UUID("bf90f3a5-e204-4373-acd1-dd24e1eb58f3"),
            display_name="Mason Gonzalez",
            first_name="Mason",
            last_name="Gonzalez",
            email="mason.gonzalez12@example.com",
        ),
        User(
            id=UUID("bfd9708f-d51b-4fe1-bfcc-ca8cb2830a7d"),
            display_name="Layla Wilson",
            first_name="Layla",
            last_name="Wilson",
            email="layla.wilson13@example.com",
        ),
        User(
            id=UUID("c3ed02b5-b175-4ab8-b153-640c4e8dbfa6"),
            display_name="Logan Anderson",
            first_name="Logan",
            last_name="Anderson",
            email="logan.anderson14@example.com",
        ),
        User(
            id=UUID("2911b7f6-3d3f-4d03-a09e-0bfe013ef161"),
            display_name="Aria Thomas",
            first_name="Aria",
            last_name="Thomas",
            email="aria.thomas15@example.com",
        ),
        User(
            id=UUID("3529c963-84c7-4e26-8017-b1805d0a4280"),
            display_name="Elijah Taylor",
            first_name="Elijah",
            last_name="Taylor",
            email="elijah.taylor16@example.com",
        ),
        User(
            id=UUID("54839cd2-c8fb-47ca-a9f0-fbfd73046582"),
            display_name="Mia Moore",
            first_name="Mia",
            last_name="Moore",
            email="mia.moore17@example.com",
        ),
        User(
            id=UUID("55391432-b85d-4479-8b03-71029cc4a76a"),
            display_name="Jayden Jackson",
            first_name="Jayden",
            last_name="Jackson",
            email="jayden.jackson18@example.com",
        ),
        User(
            id=UUID("9a9c45d7-1891-48c3-aad8-a328c0eca705"),
            display_name="Zoe Martin",
            first_name="Zoe",
            last_name="Martin",
            email="zoe.martin19@example.com",
        ),
        User(
            id=UUID("c12f41cd-8bd2-4c1d-896d-16e33d0df389"),
            display_name="Aiden Lee",
            first_name="Aiden",
            last_name="Lee",
            email="aiden.lee20@example.com",
        ),
        User(
            id=UUID("d43f9db4-b2bd-477c-98ba-07de383d867a"),
            display_name="Harper Perez",
            first_name="Harper",
            last_name="Perez",
            email="harper.perez21@example.com",
        ),
        User(
            id=UUID("21658b93-8b33-4921-9b7b-715b34a1461a"),
            display_name="Daniel Thompson",
            first_name="Daniel",
            last_name="Thompson",
            email="daniel.thompson22@example.com",
        ),
        User(
            id=UUID("f9a12ff2-21ca-4ad5-b3ea-80911709726c"),
            display_name="Ella White",
            first_name="Ella",
            last_name="White",
            email="ella.white23@example.com",
        ),
        User(
            id=UUID("35c42278-c7ee-4680-b67b-65658e2438e6"),
            display_name="Benjamin Harris",
            first_name="Benjamin",
            last_name="Harris",
            email="benjamin.harris24@example.com",
        ),
        User(
            id=UUID("0837cf2f-c000-4d8c-8ec1-7aa38af5e236"),
            display_name="Grace Sanchez",
            first_name="Grace",
            last_name="Sanchez",
            email="grace.sanchez25@example.com",
        ),
        User(
            id=UUID("7ca2be93-1698-419a-9d8e-066dc81deb7c"),
            display_name="Samuel Clark",
            first_name="Samuel",
            last_name="Clark",
            email="samuel.clark26@example.com",
        ),
        User(
            id=UUID("685cb5b2-2a60-4951-840a-114e6db46905"),
            display_name="Lily Ramirez",
            first_name="Lily",
            last_name="Ramirez",
            email="lily.ramirez27@example.com",
        ),
        User(
            id=UUID("a99a2fba-9fad-4650-82a7-5dfd4398b0b0"),
            display_name="Henry Lewis",
            first_name="Henry",
            last_name="Lewis",
            email="henry.lewis28@example.com",
        ),
        User(
            id=UUID("bbd27b45-b5f3-4aa9-b21a-b07f5d9de9f7"),
            display_name="Avery Robinson",
            first_name="Avery",
            last_name="Robinson",
            email="avery.robinson29@example.com",
        ),
        User(
            id=UUID("2fdc08c9-0264-4e1f-80ff-0625bf2e8cfe"),
            display_name="Jack Walker",
            first_name="Jack",
            last_name="Walker",
            email="jack.walker30@example.com",
        ),
        User(
            id=UUID("f52711be-8b3e-4757-b856-de1aa74acb5f"),
            display_name="Evelyn Young",
            first_name="Evelyn",
            last_name="Young",
            email="evelyn.young31@example.com",
        ),
        User(
            id=UUID("346e81a4-9470-4230-ab97-452e9dec447d"),
            display_name="Owen Allen",
            first_name="Owen",
            last_name="Allen",
            email="owen.allen32@example.com",
        ),
        User(
            id=UUID("5e2891be-eaec-4ce1-a817-72613c5c167e"),
            display_name="Abigail King",
            first_name="Abigail",
            last_name="King",
            email="abigail.king33@example.com",
        ),
        User(
            id=UUID("bad3c6c0-e362-4461-9d00-e4f30126a1e6"),
            display_name="Sam Wright",
            first_name="Sam",
            last_name="Wright",
            email="sam.wright34@example.com",
        ),
        User(
            id=UUID("eb29e535-9e86-4b79-af06-baf174990004"),
            display_name="Emily Scott",
            first_name="Emily",
            last_name="Scott",
            email="emily.scott35@example.com",
        ),
        User(
            id=UUID("af378101-2a61-43d7-8aec-5479b2ac4a03"),
            display_name="Leo Torres",
            first_name="Leo",
            last_name="Torres",
            email="leo.torres36@example.com",
        ),
        User(
            id=UUID("e7eb73ec-c6ac-48ca-b781-6492307a5eb2"),
            display_name="Charlotte Nguyen",
            first_name="Charlotte",
            last_name="Nguyen",
            email="charlotte.nguyen37@example.com",
        ),
        User(
            id=UUID("cf43748d-f2fa-4763-8d7a-82c93b45c23f"),
            display_name="Caleb Hill",
            first_name="Caleb",
            last_name="Hill",
            email="caleb.hill38@example.com",
        ),
        User(
            id=UUID("ee409a63-ea67-4026-8b67-cbe3155f6f15"),
            display_name="Amelia Flores",
            first_name="Amelia",
            last_name="Flores",
            email="amelia.flores39@example.com",
        ),
        User(
            id=UUID("ef27f0e0-8ff7-49a5-ad6d-92f97257849a"),
            display_name="Ryan Green",
            first_name="Ryan",
            last_name="Green",
            email="ryan.green40@example.com",
        ),
        User(
            id=UUID("532e5da4-0fde-4c4f-b8a9-21af37513a90"),
            display_name="Madison Adams",
            first_name="Madison",
            last_name="Adams",
            email="madison.adams41@example.com",
        ),
        User(
            id=UUID("aba1901e-ae2e-4515-9402-b25b84dcb482"),
            display_name="Nathan Nelson",
            first_name="Nathan",
            last_name="Nelson",
            email="nathan.nelson42@example.com",
        ),
        User(
            id=UUID("886ec931-d5d4-4c66-893b-373fe5ad5a93"),
            display_name="Ella Baker",
            first_name="Ella",
            last_name="Baker",
            email="ella.baker43@example.com",
        ),
        User(
            id=UUID("14bcf231-2818-4ff9-8222-6f63f7e65809"),
            display_name="Aaron Hall",
            first_name="Aaron",
            last_name="Hall",
            email="aaron.hall44@example.com",
        ),
        User(
            id=UUID("947c2e18-c1e1-4d34-937f-ff62c375229a"),
            display_name="Scarlett Rivera",
            first_name="Scarlett",
            last_name="Rivera",
            email="scarlett.rivera45@example.com",
        ),
        User(
            id=UUID("2d63f888-8b83-4c38-9953-15f61347732e"),
            display_name="Adrian Campbell",
            first_name="Adrian",
            last_name="Campbell",
            email="adrian.campbell46@example.com",
        ),
        User(
            id=UUID("5ecbfff1-c5ba-491b-a0aa-de881b0349cb"),
            display_name="Victoria Mitchell",
            first_name="Victoria",
            last_name="Mitchell",
            email="victoria.mitchell47@example.com",
        ),
        User(
            id=UUID("f99e9128-e51e-4b1d-b8f2-ea83f2d4b90b"),
            display_name="Cameron Carter",
            first_name="Cameron",
            last_name="Carter",
            email="cameron.carter48@example.com",
        ),
        User(
            id=UUID("426875ac-13f2-4d1c-b0ea-fe34b2a8c959"),
            display_name="Nora Roberts",
            first_name="Nora",
            last_name="Roberts",
            email="nora.roberts49@example.com",
        ),
    ]

    addresses = [
        Address(
            id=UUID("fdb0140f-fee0-4ffc-a0ca-1cbaaff1294e"),
            account_id=UUID("eec50538-0edc-469b-b441-01b95b2f86c1"),
            line_1="200 Bloor St. E.",
            city="Whitehorse",
            province="Yukon",
            postal_code="A4K 3G1",
        ),
        Address(
            id=UUID("2abc62b5-8df0-4a1f-8355-f774be347fa4"),
            account_id=UUID("cd1e919c-78ac-4222-96c1-6bea98f57281"),
            line_1="1550 Market Ave.",
            city="Whitehorse",
            province="Yukon",
            postal_code="Y6B 0C3",
        ),
        Address(
            id=UUID("d944e742-faca-49e5-b28c-ae506a5e95cb"),
            account_id=UUID("63363a5a-f35b-4b76-84b0-aa354843e426"),
            line_1="12 Harbourfront Rd.",
            city="Winnipeg",
            province="Manitoba",
            postal_code="X3X 6K7",
        ),
        Address(
            id=UUID("145433e4-79ef-4bdd-9985-d5f21aecad25"),
            account_id=UUID("75e4418a-1216-4988-afd0-74db0f4d121f"),
            line_1="888 Robson St.",
            city="St. John's",
            province="Newfoundland and Labrador",
            postal_code="A2S 5L2",
        ),
        Address(
            id=UUID("40040d00-1975-4af5-8197-1b8e722945f3"),
            account_id=UUID("bb355aea-9041-4fc3-b0ff-cd55a8fb6a46"),
            line_1="350 Rue Saint-Paul O.",
            city="Winnipeg",
            province="Manitoba",
            postal_code="E1R 1P5",
        ),
        Address(
            id=UUID("8679ba64-4472-42d4-b7e8-9cf8a53ee093"),
            account_id=UUID("521df1bc-8a74-40c7-a768-c41dcf49e02b"),
            line_1="250 Rue Saint-Paul O.",
            city="St. John's",
            province="Newfoundland and Labrador",
            postal_code="B7X 1R1",
        ),
        Address(
            id=UUID("2ac9edaf-d154-4024-9386-ff4ef924d2be"),
            account_id=UUID("e9706931-6932-4a7c-9a48-0c81728b4ee0"),
            line_1="15 Rue Sainte-Anne",
            city="Charlottetown",
            province="Prince Edward Island",
            postal_code="Z5Y 3C0",
        ),
        Address(
            id=UUID("a14c2e1d-cbb7-4af5-8005-e36dbb77ab10"),
            account_id=UUID("3f7b69d9-8908-4350-b7f4-eb3bcb303455"),
            line_1="77 Rue du Marché Champlain",
            city="Whitehorse",
            province="Yukon",
            postal_code="M1K 1R4",
        ),
        Address(
            id=UUID("7c076012-5ddc-4173-9c1b-59a8b27d33e3"),
            account_id=UUID("7094965f-be3d-49db-8a3d-c8e1bc8b3f99"),
            line_1="Cedar Ridge Dr.",
            city="Halifax",
            province="Nova Scotia",
            postal_code="H5P 3L1",
        ),
        Address(
            id=UUID("b9fa5862-bf7d-405a-be3e-94c3d40b95b7"),
            account_id=UUID("6f04f89b-e24a-43ac-8bb4-4b692db482ba"),
            line_1="33 Portage Ave.",
            city="St. John's",
            province="Newfoundland and Labrador",
            postal_code="X3H 7R4",
        ),
        Address(
            id=UUID("ab662ec2-7a54-415a-ba08-d6b92c1fa2e5"),
            account_id=UUID("94f35ca2-5e50-4cde-b814-37c8169c0614"),
            line_1="77 Rue du Marché Champlain",
            city="Whitehorse",
            province="Yukon",
            postal_code="N0K 0N6",
        ),
        Address(
            id=UUID("9b1554f1-e8fe-40f6-977d-6f7fef50efa9"),
            account_id=UUID("0daec970-3840-4aad-b2fb-05c1e4fa635d"),
            line_1="4201 Bank St.",
            city="Toronto",
            province="Ontario",
            postal_code="J9N 3V6",
        ),
        Address(
            id=UUID("0db92c9e-8cec-44f7-be04-2019923db5f1"),
            account_id=UUID("bf90f3a5-e204-4373-acd1-dd24e1eb58f3"),
            line_1="Aspen Grove",
            city="Whitehorse",
            province="Yukon",
            postal_code="G4G 3X8",
        ),
        Address(
            id=UUID("de4a2b73-3328-4a0f-9541-7f114e4b3a31"),
            account_id=UUID("bfd9708f-d51b-4fe1-bfcc-ca8cb2830a7d"),
            line_1="Pinecrest Way",
            city="Toronto",
            province="Ontario",
            postal_code="Y6P 3G8",
        ),
        Address(
            id=UUID("fd090913-d917-467d-b3a5-5e9b9e3e48e5"),
            account_id=UUID("c3ed02b5-b175-4ab8-b153-640c4e8dbfa6"),
            line_1="1550 Market Ave.",
            city="Halifax",
            province="Nova Scotia",
            postal_code="B1G 2S9",
        ),
        Address(
            id=UUID("a0f86108-9b88-4da8-8d83-ac171b63dd3a"),
            account_id=UUID("2911b7f6-3d3f-4d03-a09e-0bfe013ef161"),
            line_1="Willowbrook Ct.",
            city="Edmonton",
            province="Alberta",
            postal_code="R9T 8L8",
        ),
        Address(
            id=UUID("deed70ce-32c8-4bdf-b3a5-3722615ef91d"),
            account_id=UUID("3529c963-84c7-4e26-8017-b1805d0a4280"),
            line_1="200 Bloor St. E.",
            city="Victoria",
            province="British Columbia",
            postal_code="X4N 1M6",
        ),
        Address(
            id=UUID("9d3608f3-2737-425c-b93a-cf3a183cd372"),
            account_id=UUID("54839cd2-c8fb-47ca-a9f0-fbfd73046582"),
            line_1="Aspen Grove",
            city="Regina",
            province="Saskatchewan",
            postal_code="A4W 2W1",
        ),
        Address(
            id=UUID("c50328f8-3d16-4ea2-9b10-e19b310a4ffa"),
            account_id=UUID("55391432-b85d-4479-8b03-71029cc4a76a"),
            line_1="600 Rue Saint-Jean",
            city="Whitehorse",
            province="Yukon",
            postal_code="W9J 2P2",
        ),
        Address(
            id=UUID("7f9c2dd5-d057-41e8-8896-ae767a59f46e"),
            account_id=UUID("9a9c45d7-1891-48c3-aad8-a328c0eca705"),
            line_1="941 Progress Ave.",
            city="Charlottetown",
            province="Prince Edward Island",
            postal_code="Z5V 0E5",
        ),
        Address(
            id=UUID("f3b4b480-0812-419e-9b15-788ccf9ab871"),
            account_id=UUID("c12f41cd-8bd2-4c1d-896d-16e33d0df389"),
            line_1="600 Rue Saint-Jean",
            city="Iqaluit",
            province="Nunavut",
            postal_code="K0K 9C1",
        ),
        Address(
            id=UUID("6d210d3c-9282-4a3f-9e5c-6651d010e6e5"),
            account_id=UUID("d43f9db4-b2bd-477c-98ba-07de383d867a"),
            line_1="Lakeshore Blvd.",
            city="Yellowknife",
            province="Northwest Territories",
            postal_code="C8G 2V8",
        ),
        Address(
            id=UUID("f10c945b-7f0f-4602-9898-5c8ad65b8c52"),
            account_id=UUID("21658b93-8b33-4921-9b7b-715b34a1461a"),
            line_1="250 Rue Saint-Paul O.",
            city="Regina",
            province="Saskatchewan",
            postal_code="W9S 3X3",
        ),
        Address(
            id=UUID("1b00e985-9886-4677-9f57-04f8e6645378"),
            account_id=UUID("f9a12ff2-21ca-4ad5-b3ea-80911709726c"),
            line_1="600 Rue Saint-Jean",
            city="Yellowknife",
            province="Northwest Territories",
            postal_code="R5T 8T1",
        ),
        Address(
            id=UUID("94ee5a16-0376-4564-a5ac-153cb0594df8"),
            account_id=UUID("35c42278-c7ee-4680-b67b-65658e2438e6"),
            line_1="77 Rue du Marché Champlain",
            city="Winnipeg",
            province="Manitoba",
            postal_code="C5A 9X3",
        ),
        Address(
            id=UUID("e87f3127-d7f5-4662-9f94-904a8fd725bb"),
            account_id=UUID("0837cf2f-c000-4d8c-8ec1-7aa38af5e236"),
            line_1="77 Rue du Marché Champlain",
            city="St. John's",
            province="Newfoundland and Labrador",
            postal_code="A1B 3C0",
        ),
        Address(
            id=UUID("5dcca33c-2912-4112-b8d5-066352c7d5a2"),
            account_id=UUID("7ca2be93-1698-419a-9d8e-066dc81deb7c"),
            line_1="4201 Bank St.",
            city="Quebec City",
            province="Quebec",
            postal_code="W3L 7J8",
        ),
        Address(
            id=UUID("0a17ec86-f797-4f62-bf35-5ed555982f81"),
            account_id=UUID("685cb5b2-2a60-4951-840a-114e6db46905"),
            line_1="Sycamore Cres.",
            city="Regina",
            province="Saskatchewan",
            postal_code="K7S 3E1",
        ),
        Address(
            id=UUID("8e900b21-7a8d-4aaf-a414-2c33050af742"),
            account_id=UUID("a99a2fba-9fad-4650-82a7-5dfd4398b0b0"),
            line_1="Pinecrest Way",
            city="Whitehorse",
            province="Yukon",
            postal_code="P6S 7B1",
        ),
        Address(
            id=UUID("570fd1ca-724f-4466-ba20-373650655d97"),
            account_id=UUID("bbd27b45-b5f3-4aa9-b21a-b07f5d9de9f7"),
            line_1="Oakwood Ave.",
            city="Victoria",
            province="British Columbia",
            postal_code="N1K 3J8",
        ),
        Address(
            id=UUID("299828c0-0370-4fbd-b388-92e0710d81a2"),
            account_id=UUID("2fdc08c9-0264-4e1f-80ff-0625bf2e8cfe"),
            line_1="61 O'Connell St.",
            city="Halifax",
            province="Nova Scotia",
            postal_code="S2L 7K1",
        ),
        Address(
            id=UUID("eeb1f7e9-1814-4dca-9bfa-6e4d4808564d"),
            account_id=UUID("f52711be-8b3e-4757-b856-de1aa74acb5f"),
            line_1="88 Granville St.",
            city="Halifax",
            province="Nova Scotia",
            postal_code="B8A 1K2",
        ),
        Address(
            id=UUID("25a3f6a4-d6ae-4c7e-85d2-7d892d904628"),
            account_id=UUID("346e81a4-9470-4230-ab97-452e9dec447d"),
            line_1="Lakeshore Blvd.",
            city="Fredericton",
            province="New Brunswick",
            postal_code="V3R 0H6",
        ),
        Address(
            id=UUID("66f20ef3-e69a-495c-b443-7866146d59fa"),
            account_id=UUID("5e2891be-eaec-4ce1-a817-72613c5c167e"),
            line_1="Willowbrook Ct.",
            city="Victoria",
            province="British Columbia",
            postal_code="L7M 6X7",
        ),
        Address(
            id=UUID("c8c4a646-62ac-4027-9582-2d3ad422a5ca"),
            account_id=UUID("bad3c6c0-e362-4461-9d00-e4f30126a1e6"),
            line_1="505 Rue Laurier O.",
            city="Regina",
            province="Saskatchewan",
            postal_code="M3B 9X0",
        ),
        Address(
            id=UUID("7c33612b-a93b-413c-ba9f-2291780e77c5"),
            account_id=UUID("eb29e535-9e86-4b79-af06-baf174990004"),
            line_1="12 Rue du Carrefour",
            city="Yellowknife",
            province="Northwest Territories",
            postal_code="B0Y 7W8",
        ),
        Address(
            id=UUID("ad0aed80-135d-4945-8463-086596f76595"),
            account_id=UUID("af378101-2a61-43d7-8aec-5479b2ac4a03"),
            line_1="78 King St. W.",
            city="Regina",
            province="Saskatchewan",
            postal_code="W1H 1Z1",
        ),
        Address(
            id=UUID("cb95a3ac-ae57-43dd-8245-31471b6782fb"),
            account_id=UUID("e7eb73ec-c6ac-48ca-b781-6492307a5eb2"),
            line_1="40 Wellington St.",
            city="Whitehorse",
            province="Yukon",
            postal_code="R1Y 3Y9",
        ),
        Address(
            id=UUID("41a84593-3188-45c7-9c0b-31ad9b8a4641"),
            account_id=UUID("cf43748d-f2fa-4763-8d7a-82c93b45c23f"),
            line_1="1550 Market Ave.",
            city="Victoria",
            province="British Columbia",
            postal_code="S9Y 8N4",
        ),
        Address(
            id=UUID("bbfe8e40-e14f-4e6a-ab0e-675306c76a68"),
            account_id=UUID("ee409a63-ea67-4026-8b67-cbe3155f6f15"),
            line_1="12 Rue du Carrefour",
            city="Winnipeg",
            province="Manitoba",
            postal_code="K4R 2M7",
        ),
        Address(
            id=UUID("eaca8cba-101e-4042-8805-3258d1ff7d36"),
            account_id=UUID("ef27f0e0-8ff7-49a5-ad6d-92f97257849a"),
            line_1="4201 Bank St.",
            city="Quebec City",
            province="Quebec",
            postal_code="A7Z 9E1",
        ),
        Address(
            id=UUID("2eaa5a10-d3a4-4e0a-815f-1c2df118caae"),
            account_id=UUID("532e5da4-0fde-4c4f-b8a9-21af37513a90"),
            line_1="1234 8th Ave. SW",
            city="Charlottetown",
            province="Prince Edward Island",
            postal_code="W4G 5C3",
        ),
        Address(
            id=UUID("0c976513-19c1-45db-9632-32128b2621f6"),
            account_id=UUID("aba1901e-ae2e-4515-9402-b25b84dcb482"),
            line_1="15 Rue Sainte-Anne",
            city="Quebec City",
            province="Quebec",
            postal_code="H7X 4Z8",
        ),
        Address(
            id=UUID("ac76a5ad-7dd6-4f45-b245-0741ebdf5620"),
            account_id=UUID("886ec931-d5d4-4c66-893b-373fe5ad5a93"),
            line_1="600 Rue Saint-Jean",
            city="Victoria",
            province="British Columbia",
            postal_code="E2L 1E8",
        ),
        Address(
            id=UUID("64bbdc4d-405f-4243-8425-c2715676e11b"),
            account_id=UUID("14bcf231-2818-4ff9-8222-6f63f7e65809"),
            line_1="888 Robson St.",
            city="Regina",
            province="Saskatchewan",
            postal_code="M9J 5J4",
        ),
        Address(
            id=UUID("5c24ff74-b6da-4075-aba2-5cf97cbb79f6"),
            account_id=UUID("947c2e18-c1e1-4d34-937f-ff62c375229a"),
            line_1="Lakeshore Blvd.",
            city="Charlottetown",
            province="Prince Edward Island",
            postal_code="L0C 6L0",
        ),
        Address(
            id=UUID("124244e3-9aaa-498c-8f1e-52fc3aedf3e1"),
            account_id=UUID("2d63f888-8b83-4c38-9953-15f61347732e"),
            line_1="350 Rue Saint-Paul O.",
            city="Victoria",
            province="British Columbia",
            postal_code="G4H 7X6",
        ),
        Address(
            id=UUID("3c8914a3-ea8f-4e33-83d6-0c258599e6d5"),
            account_id=UUID("5ecbfff1-c5ba-491b-a0aa-de881b0349cb"),
            line_1="941 Progress Ave.",
            city="Charlottetown",
            province="Prince Edward Island",
            postal_code="E1G 8B5",
        ),
        Address(
            id=UUID("3a68343c-1224-44aa-85cd-b6876e1d96b7"),
            account_id=UUID("f99e9128-e51e-4b1d-b8f2-ea83f2d4b90b"),
            line_1="901 Barrington St.",
            city="St. John's",
            province="Newfoundland and Labrador",
            postal_code="S2B 4P0",
        ),
        Address(
            id=UUID("20b5d406-32b8-4c91-aa19-2c52c9c615a6"),
            account_id=UUID("426875ac-13f2-4d1c-b0ea-fe34b2a8c959"),
            line_1="1234 8th Ave. SW",
            city="Quebec City",
            province="Quebec",
            postal_code="K1P 8S9",
        ),
    ]

    organizations = [
        Organization(
            id=UUID("2cbd7222-4fd3-4cef-9500-79746e76da89"),
            display_name="Éclair Events",
        ),
        Organization(
            id=UUID("8e21c0af-d7a0-4f06-940c-b23728ae59e1"),
            display_name="Lopezs Event Planning and Decor",
        ),
        Organization(
            id=UUID("7092b056-4bec-4f3e-aec4-7f7e8f37b13d"),
            display_name="Golden Hour Gatherings",
        ),
        Organization(
            id=UUID("f729f07d-833d-48e3-97e3-61d360b18e2e"),
            display_name="The Grand Occasion Co.",
        ),
        Organization(
            id=UUID("dbdf610b-3e5e-4565-b12a-707eb57b8b35"),
            display_name="Evergreen Celebrations Ltd.",
        ),
    ]

    organization_members = [
        OrganizationMember(
            organization_id=UUID("2cbd7222-4fd3-4cef-9500-79746e76da89"),
            account_id=UUID("2911b7f6-3d3f-4d03-a09e-0bfe013ef161"),
            permissions=0,
        ),
        OrganizationMember(
            organization_id=UUID("8e21c0af-d7a0-4f06-940c-b23728ae59e1"),
            account_id=UUID("0daec970-3840-4aad-b2fb-05c1e4fa635d"),
            permissions=0,
        ),
        OrganizationMember(
            organization_id=UUID("7092b056-4bec-4f3e-aec4-7f7e8f37b13d"),
            account_id=UUID("cd1e919c-78ac-4222-96c1-6bea98f57281"),
            permissions=0,
        ),
        OrganizationMember(
            organization_id=UUID("7092b056-4bec-4f3e-aec4-7f7e8f37b13d"),
            account_id=UUID("5ecbfff1-c5ba-491b-a0aa-de881b0349cb"),
            permissions=0,
        ),
        OrganizationMember(
            organization_id=UUID("f729f07d-833d-48e3-97e3-61d360b18e2e"),
            account_id=UUID("7ca2be93-1698-419a-9d8e-066dc81deb7c"),
            permissions=0,
        ),
        OrganizationMember(
            organization_id=UUID("f729f07d-833d-48e3-97e3-61d360b18e2e"),
            account_id=UUID("aba1901e-ae2e-4515-9402-b25b84dcb482"),
            permissions=0,
        ),
        OrganizationMember(
            organization_id=UUID("dbdf610b-3e5e-4565-b12a-707eb57b8b35"),
            account_id=UUID("54839cd2-c8fb-47ca-a9f0-fbfd73046582"),
            permissions=0,
        ),
    ]

    venues = [
        Venue(
            id=UUID("9b87e7a8-aa6b-4c60-a25b-158e1577ff25"),
            organization_id=UUID("2cbd7222-4fd3-4cef-9500-79746e76da89"),
            display_name="Éclair Events - Venue 1",
            description="""## About
A beautiful event space featuring **floor-to-ceiling windows** and modern amenities.

## Features
- Capacity: 200 guests
- AV equipment included
- On-site parking

## Ideal for
Weddings, corporate events, and private parties.""",
            location_name="88 Granville St.",
        ),
        Venue(
            id=UUID("d60f59fc-721d-42bb-8a35-821de7cdc7d8"),
            organization_id=UUID("8e21c0af-d7a0-4f06-940c-b23728ae59e1"),
            display_name="Lopez's Event Planning and Decor - Venue 1",
            description="""## About
A charming rustic venue with exposed brick walls and **warm lighting**.

## Features
- Capacity: 150 guests
- Outdoor courtyard
- Full kitchen access

## Ideal for
Intimate weddings, birthday celebrations, and small conferences.""",
            location_name="Sycamore Cres.",
        ),
        Venue(
            id=UUID("fbacc99d-7e4c-42fb-8032-a974ff512649"),
            organization_id=UUID("8e21c0af-d7a0-4f06-940c-b23728ae59e1"),
            display_name="Lopez's Event Planning and Decor - Venue 2",
            description="""## About
A state-of-the-art conference center with **flexible seating** and cutting-edge technology.

## Features
- Capacity: 500 guests
- Breakout rooms
- Business center

## Ideal for
Conferences, product launches, and large corporate gatherings.""",
            location_name="505 Rue Laurier O.",
        ),
        Venue(
            id=UUID("1fb94585-3991-4d5b-817f-8aed59c3218d"),
            organization_id=UUID("7092b056-4bec-4f3e-aec4-7f7e8f37b13d"),
            display_name="Golden Hour Gatherings - Venue 1",
            description="""## About
A stunning waterfront venue offering **panoramic views** and elegant décor.

## Features
- Capacity: 300 guests
- Outdoor terrace
- Bridal suite

## Ideal for
Weddings, anniversary parties, and upscale dinners.""",
            location_name="600 Rue Saint-Jean",
        ),
        Venue(
            id=UUID("a70927b2-ffa4-4c76-a79f-7f308cb1f568"),
            organization_id=UUID("7092b056-4bec-4f3e-aec4-7f7e8f37b13d"),
            display_name="Golden Hour Gatherings - Venue 2",
            description="""## About
A versatile community hall with **customizable layouts** and affordable pricing.

## Features
- Capacity: 100 guests
- Stage available
- Kitchen facilities

## Ideal for
Community events, workshops, and birthday parties.""",
            location_name="77 Rue du Marché Champlain",
        ),
        Venue(
            id=UUID("9558cd33-30bd-47b5-bbee-5360e524cd02"),
            organization_id=UUID("f729f07d-833d-48e3-97e3-61d360b18e2e"),
            display_name="The Grand Occasion Co. - Venue 1",
            description="""## About
A beautiful event space featuring **floor-to-ceiling windows** and modern amenities.

## Features
- Capacity: 200 guests
- AV equipment included
- On-site parking

## Ideal for
Weddings, corporate events, and private parties.""",
            location_name="505 Rue Laurier O.",
        ),
        Venue(
            id=UUID("bc96927a-7495-415f-965a-ca00ffda7fc0"),
            organization_id=UUID("dbdf610b-3e5e-4565-b12a-707eb57b8b35"),
            display_name="Evergreen Celebrations Ltd. - Venue 1",
            description="""## About
A charming rustic venue with exposed brick walls and **warm lighting**.

## Features
- Capacity: 150 guests
- Outdoor courtyard
- Full kitchen access

## Ideal for
Intimate weddings, birthday celebrations, and small conferences.""",
            location_name="888 Robson St.",
        ),
        Venue(
            id=UUID("820c4849-2bdc-40e5-a3df-726a091544a6"),
            organization_id=UUID("dbdf610b-3e5e-4565-b12a-707eb57b8b35"),
            display_name="Evergreen Celebrations Ltd. - Venue 2",
            description="""## About
A state-of-the-art conference center with **flexible seating** and cutting-edge technology.

## Features
- Capacity: 500 guests
- Breakout rooms
- Business center

## Ideal for
Conferences, product launches, and large corporate gatherings.""",
            location_name="888 Robson St.",
        ),
    ]

    events = [
        Event(
            id=UUID("df7b2a4c-6647-43b7-88c7-17ddd2a43080"),
            venue_id=UUID("9b87e7a8-aa6b-4c60-a25b-158e1577ff25"),
            display_name="Event 1 at Éclair Events",
            description="""## Annual Gala
Join us for an **elegant evening** of dinner, dancing, and live entertainment.

- **Date:** Saturday, March 15th
- **Time:** 6:00 PM - 11:00 PM
- **Dress code:** Black tie optional

## Tickets
- General Admission: $75
- VIP Table: $500 (seats 8)""",
        ),
        Event(
            id=UUID("ad1d67bd-d92c-41e8-8494-c943eaaac05a"),
            venue_id=UUID("9b87e7a8-aa6b-4c60-a25b-158e1577ff25"),
            display_name="Event 2 at Éclair Events",
            description="""## Corporate Conference 2024
A full-day conference featuring **industry leaders** and networking opportunities.

- **Date:** Thursday, April 22nd
- **Time:** 9:00 AM - 5:00 PM
- **Lunch:** Included

## Topics
- Digital Transformation
- Sustainable Business
- Leadership in Uncertain Times""",
        ),
        Event(
            id=UUID("0e161235-9c40-45e6-b4cd-022fd852f6e6"),
            venue_id=UUID("d60f59fc-721d-42bb-8a35-821de7cdc7d8"),
            display_name="Event 3 at Lopezs Event Planning and Decor",
            description="""## Summer Wedding Expo
Discover the latest trends in **wedding planning**, décor, and catering.

- **Date:** Saturday, June 8th
- **Time:** 11:00 AM - 4:00 PM
- **Admission:** Free

## Features
- Live demonstrations
- Vendor booths
- Fashion show""",
        ),
        Event(
            id=UUID("21afa1a9-a4ed-4d2f-8908-93b743027fec"),
            venue_id=UUID("d60f59fc-721d-42bb-8a35-821de7cdc7d8"),
            display_name="Event 4 at Lopezs Event Planning and Decor",
            description="""## Charity Dinner
An evening dedicated to supporting **local causes** through fine dining and auctions.

- **Date:** Friday, September 20th
- **Time:** 7:00 PM - 10:00 PM
- **Ticket Price:** $120

## Proceeds benefit
- Children''s Hospital
- Local Food Bank
- Environmental Fund""",
        ),
        Event(
            id=UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
            venue_id=UUID("d60f59fc-721d-42bb-8a35-821de7cdc7d8"),
            display_name="Event 5 at Lopezs Event Planning and Decor",
            description="""## New Year''s Eve Party
Ring in the new year with **champagne, fireworks**, and dancing until midnight.

- **Date:** December 31st
- **Time:** 9:00 PM - 2:00 AM
- **Ticket Price:** $150

## Includes
- Open bar
- Live DJ
- Midnight toast""",
        ),
        Event(
            id=UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
            venue_id=UUID("fbacc99d-7e4c-42fb-8032-a974ff512649"),
            display_name="Event 6 at Lopezs Event Planning and Decor",
            description="""## Annual Gala
Join us for an **elegant evening** of dinner, dancing, and live entertainment.

- **Date:** Saturday, March 15th
- **Time:** 6:00 PM - 11:00 PM
- **Dress code:** Black tie optional

## Tickets
- General Admission: $75
- VIP Table: $500 (seats 8)""",
        ),
        Event(
            id=UUID("5a1231e3-8e9a-4e87-9835-6db515975d7c"),
            venue_id=UUID("fbacc99d-7e4c-42fb-8032-a974ff512649"),
            display_name="Event 7 at Lopezs Event Planning and Decor",
            description="""## Corporate Conference 2024
A full-day conference featuring **industry leaders** and networking opportunities.

- **Date:** Thursday, April 22nd
- **Time:** 9:00 AM - 5:00 PM
- **Lunch:** Included

## Topics
- Digital Transformation
- Sustainable Business
- Leadership in Uncertain Times""",
        ),
        Event(
            id=UUID("697102d3-6f53-4c93-b65b-f87a36a9b301"),
            venue_id=UUID("9558cd33-30bd-47b5-bbee-5360e524cd02"),
            display_name="Event 8 at The Grand Occasion Co.",
            description="""## Summer Wedding Expo
Discover the latest trends in **wedding planning**, décor, and catering.

- **Date:** Saturday, June 8th
- **Time:** 11:00 AM - 4:00 PM
- **Admission:** Free

## Features
- Live demonstrations
- Vendor booths
- Fashion show""",
        ),
        Event(
            id=UUID("df8af935-6315-4a0f-9723-e4b031458a4d"),
            venue_id=UUID("9558cd33-30bd-47b5-bbee-5360e524cd02"),
            display_name="Event 9 at The Grand Occasion Co.",
            description="""## Charity Dinner
An evening dedicated to supporting **local causes** through fine dining and auctions.

- **Date:** Friday, September 20th
- **Time:** 7:00 PM - 10:00 PM
- **Ticket Price:** $120

## Proceeds benefit
- Children''s Hospital
- Local Food Bank
- Environmental Fund""",
        ),
        Event(
            id=UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
            venue_id=UUID("bc96927a-7495-415f-965a-ca00ffda7fc0"),
            display_name="Event 10 at Evergreen Celebrations Ltd.",
            description="""## New Year''s Eve Party
Ring in the new year with **champagne, fireworks**, and dancing until midnight.

- **Date:** December 31st
- **Time:** 9:00 PM - 2:00 AM
- **Ticket Price:** $150

## Includes
- Open bar
- Live DJ
- Midnight toast""",
        ),
        Event(
            id=UUID("97067d2e-7a1c-4451-ac3a-a8e974e1c6e3"),
            venue_id=UUID("820c4849-2bdc-40e5-a3df-726a091544a6"),
            display_name="Event 11 at Evergreen Celebrations Ltd.",
            description="""## Annual Gala
Join us for an **elegant evening** of dinner, dancing, and live entertainment.

- **Date:** Saturday, March 15th
- **Time:** 6:00 PM - 11:00 PM
- **Dress code:** Black tie optional

## Tickets
- General Admission: $75
- VIP Table: $500 (seats 8)""",
        ),
        Event(
            id=UUID("ec2eb2b0-22d7-40c0-96f0-6f799227eba4"),
            venue_id=UUID("820c4849-2bdc-40e5-a3df-726a091544a6"),
            display_name="Event 12 at Evergreen Celebrations Ltd.",
            description="""## Corporate Conference 2024
A full-day conference featuring **industry leaders** and networking opportunities.

- **Date:** Thursday, April 22nd
- **Time:** 9:00 AM - 5:00 PM
- **Lunch:** Included

## Topics
- Digital Transformation
- Sustainable Business
- Leadership in Uncertain Times""",
        ),
    ]

    tickets = [
        Ticket(
            id=UUID("d8ee2ce3-c2be-4d87-ac4b-14b0e803ef0a"),
            event_id=UUID("ad1d67bd-d92c-41e8-8494-c943eaaac05a"),
            account_id=UUID("cf43748d-f2fa-4763-8d7a-82c93b45c23f"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("e1e47cf5-30b7-4246-a848-070f2d0dffa2"),
            event_id=UUID("0e161235-9c40-45e6-b4cd-022fd852f6e6"),
            account_id=UUID("21658b93-8b33-4921-9b7b-715b34a1461a"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("8b8ddfb8-e77a-4e63-8481-941e62fe2e48"),
            event_id=UUID("0e161235-9c40-45e6-b4cd-022fd852f6e6"),
            account_id=UUID("2d63f888-8b83-4c38-9953-15f61347732e"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("d3f7c0a9-f9e0-492e-bf8d-3c20f65a06e6"),
            event_id=UUID("0e161235-9c40-45e6-b4cd-022fd852f6e6"),
            account_id=UUID("c12f41cd-8bd2-4c1d-896d-16e33d0df389"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("870e7c7d-5458-4b97-a348-d47e055ed5bf"),
            event_id=UUID("0e161235-9c40-45e6-b4cd-022fd852f6e6"),
            account_id=UUID("685cb5b2-2a60-4951-840a-114e6db46905"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("643e9443-a5a3-4f81-83bc-ede7cae58954"),
            event_id=UUID("0e161235-9c40-45e6-b4cd-022fd852f6e6"),
            account_id=UUID("cf43748d-f2fa-4763-8d7a-82c93b45c23f"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("812c351b-a84d-47ad-9599-b5712f2365ac"),
            event_id=UUID("0e161235-9c40-45e6-b4cd-022fd852f6e6"),
            account_id=UUID("346e81a4-9470-4230-ab97-452e9dec447d"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("bf483a08-1945-4806-a9b7-6ffbb2d0c7ba"),
            event_id=UUID("21afa1a9-a4ed-4d2f-8908-93b743027fec"),
            account_id=UUID("35c42278-c7ee-4680-b67b-65658e2438e6"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("909a4445-86df-43e9-9cb5-071ca01b2d5e"),
            event_id=UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
            account_id=UUID("bf90f3a5-e204-4373-acd1-dd24e1eb58f3"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("a7be5b23-1b29-4037-9184-9656b8442a05"),
            event_id=UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
            account_id=UUID("3529c963-84c7-4e26-8017-b1805d0a4280"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("7ad45630-a1f5-470a-b7ab-49de01a17b09"),
            event_id=UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
            account_id=UUID("63363a5a-f35b-4b76-84b0-aa354843e426"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("beb5edd4-095e-4826-aa52-37c2d9d19f0a"),
            event_id=UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
            account_id=UUID("947c2e18-c1e1-4d34-937f-ff62c375229a"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("8fcf5095-39ba-44b8-a912-6e123f67b7bf"),
            event_id=UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
            account_id=UUID("685cb5b2-2a60-4951-840a-114e6db46905"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("cc29b74d-bf27-4d64-96ed-02843006cb0b"),
            event_id=UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
            account_id=UUID("eec50538-0edc-469b-b441-01b95b2f86c1"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("173ff694-4eb4-4580-9421-da27740baba0"),
            event_id=UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
            account_id=UUID("5e2891be-eaec-4ce1-a817-72613c5c167e"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("8f45ae59-3198-4290-acea-ecdffb5b328b"),
            event_id=UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
            account_id=UUID("bad3c6c0-e362-4461-9d00-e4f30126a1e6"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("da1b78b0-bf60-4512-8c5e-3e867b83afa8"),
            event_id=UUID("0c1ed79b-e063-45de-bfce-7283f5247bc3"),
            account_id=UUID("886ec931-d5d4-4c66-893b-373fe5ad5a93"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("4a029204-1b7b-4b2f-8e28-7d50eebe0d3e"),
            event_id=UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
            account_id=UUID("bf90f3a5-e204-4373-acd1-dd24e1eb58f3"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("41060cb5-6b94-413f-91a6-82b1e343ae24"),
            event_id=UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
            account_id=UUID("f9a12ff2-21ca-4ad5-b3ea-80911709726c"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("0687679c-6706-4c89-bff3-31f1d66ecb2d"),
            event_id=UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
            account_id=UUID("685cb5b2-2a60-4951-840a-114e6db46905"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("6d4c6f7a-ed17-43ad-a2fc-705455e9070a"),
            event_id=UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
            account_id=UUID("bb355aea-9041-4fc3-b0ff-cd55a8fb6a46"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("fc43fd85-c9fc-49f5-8aa9-97a1d59562ca"),
            event_id=UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
            account_id=UUID("aba1901e-ae2e-4515-9402-b25b84dcb482"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("253fa4c5-7d67-4622-9bd7-322cf4bd46a5"),
            event_id=UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
            account_id=UUID("d43f9db4-b2bd-477c-98ba-07de383d867a"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("1e792b54-3c3a-4c32-9e14-ac70b3bd762d"),
            event_id=UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
            account_id=UUID("ee409a63-ea67-4026-8b67-cbe3155f6f15"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("8a799cb6-414b-4dd9-87c7-5fcecf1675d8"),
            event_id=UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
            account_id=UUID("c12f41cd-8bd2-4c1d-896d-16e33d0df389"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("5535a749-ca6a-496a-a30c-69e53781f412"),
            event_id=UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
            account_id=UUID("3f7b69d9-8908-4350-b7f4-eb3bcb303455"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("8d6943e9-d8e7-4de5-aadc-2fdc0296b357"),
            event_id=UUID("ecca0ef6-390c-4b3e-9ec5-d7c307b642c5"),
            account_id=UUID("2d63f888-8b83-4c38-9953-15f61347732e"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("818abdba-3929-4b27-886c-261dc14b16a4"),
            event_id=UUID("5a1231e3-8e9a-4e87-9835-6db515975d7c"),
            account_id=UUID("346e81a4-9470-4230-ab97-452e9dec447d"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("971db374-ef1a-411a-9d05-c81e574a9b2c"),
            event_id=UUID("5a1231e3-8e9a-4e87-9835-6db515975d7c"),
            account_id=UUID("9a9c45d7-1891-48c3-aad8-a328c0eca705"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("9f4046f9-a68b-4cc2-8f80-98175775aeeb"),
            event_id=UUID("5a1231e3-8e9a-4e87-9835-6db515975d7c"),
            account_id=UUID("aba1901e-ae2e-4515-9402-b25b84dcb482"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("6a7e9f1e-1839-4dab-9b03-cb01abd63860"),
            event_id=UUID("5a1231e3-8e9a-4e87-9835-6db515975d7c"),
            account_id=UUID("7ca2be93-1698-419a-9d8e-066dc81deb7c"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("686ecb90-f1e9-4f5d-ba38-eff069400ed1"),
            event_id=UUID("697102d3-6f53-4c93-b65b-f87a36a9b301"),
            account_id=UUID("0837cf2f-c000-4d8c-8ec1-7aa38af5e236"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("daaa4b5e-0f5a-4028-96fb-95a8ba933653"),
            event_id=UUID("697102d3-6f53-4c93-b65b-f87a36a9b301"),
            account_id=UUID("14bcf231-2818-4ff9-8222-6f63f7e65809"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("70bb7583-7d65-42a5-be81-35f9476873b0"),
            event_id=UUID("697102d3-6f53-4c93-b65b-f87a36a9b301"),
            account_id=UUID("55391432-b85d-4479-8b03-71029cc4a76a"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("35dd0b3a-dfe2-4c66-a7b1-8dbc3173da77"),
            event_id=UUID("697102d3-6f53-4c93-b65b-f87a36a9b301"),
            account_id=UUID("eb29e535-9e86-4b79-af06-baf174990004"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("e710b712-4d62-4141-8cf5-30907ebe099a"),
            event_id=UUID("697102d3-6f53-4c93-b65b-f87a36a9b301"),
            account_id=UUID("7094965f-be3d-49db-8a3d-c8e1bc8b3f99"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("0fcb33f6-db23-4ff8-ba01-2e42e266183f"),
            event_id=UUID("df8af935-6315-4a0f-9723-e4b031458a4d"),
            account_id=UUID("7ca2be93-1698-419a-9d8e-066dc81deb7c"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("1fee3791-97b2-4ddb-8b6b-eab09018bd36"),
            event_id=UUID("df8af935-6315-4a0f-9723-e4b031458a4d"),
            account_id=UUID("aba1901e-ae2e-4515-9402-b25b84dcb482"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("9848ffcc-b455-4c9f-839b-e61bb71a9a89"),
            event_id=UUID("df8af935-6315-4a0f-9723-e4b031458a4d"),
            account_id=UUID("35c42278-c7ee-4680-b67b-65658e2438e6"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("b120641b-0f58-42d0-8157-6ac2fafff363"),
            event_id=UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
            account_id=UUID("5ecbfff1-c5ba-491b-a0aa-de881b0349cb"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("a1023a69-18eb-4619-97fe-2615d6ce4204"),
            event_id=UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
            account_id=UUID("0daec970-3840-4aad-b2fb-05c1e4fa635d"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("9cd09f11-d853-4c8a-94e2-aff06c010e5c"),
            event_id=UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
            account_id=UUID("ee409a63-ea67-4026-8b67-cbe3155f6f15"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("3709b088-0b95-41b2-8847-82dfbf6f01f8"),
            event_id=UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
            account_id=UUID("af378101-2a61-43d7-8aec-5479b2ac4a03"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("d1c80c0a-97a0-4fcf-905a-58aa28f2d59f"),
            event_id=UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
            account_id=UUID("9a9c45d7-1891-48c3-aad8-a328c0eca705"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("f28b01fb-d025-4a79-8622-df3cfbe000c5"),
            event_id=UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
            account_id=UUID("0837cf2f-c000-4d8c-8ec1-7aa38af5e236"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("4aed1257-7c3c-45d3-9857-c4b6d19fbc35"),
            event_id=UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
            account_id=UUID("eb29e535-9e86-4b79-af06-baf174990004"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("67cb6b35-13a7-4262-a8e3-1a49b1702f37"),
            event_id=UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
            account_id=UUID("eec50538-0edc-469b-b441-01b95b2f86c1"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("5ee78c43-029e-44d5-9f24-91c777f9105f"),
            event_id=UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
            account_id=UUID("55391432-b85d-4479-8b03-71029cc4a76a"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("bd13b575-6f08-46ba-8b0f-28e25e76cf09"),
            event_id=UUID("8f691e68-a0b5-452e-9e27-4b0161dcc62a"),
            account_id=UUID("bfd9708f-d51b-4fe1-bfcc-ca8cb2830a7d"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("17f4d2b9-8306-4e88-984d-6c4a0670c0a9"),
            event_id=UUID("97067d2e-7a1c-4451-ac3a-a8e974e1c6e3"),
            account_id=UUID("e7eb73ec-c6ac-48ca-b781-6492307a5eb2"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("7b0dbbc9-0a9a-494a-b313-ebc13ae48ebd"),
            event_id=UUID("97067d2e-7a1c-4451-ac3a-a8e974e1c6e3"),
            account_id=UUID("cf43748d-f2fa-4763-8d7a-82c93b45c23f"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("0da9a162-509f-483e-9851-e9475f8951e8"),
            event_id=UUID("97067d2e-7a1c-4451-ac3a-a8e974e1c6e3"),
            account_id=UUID("532e5da4-0fde-4c4f-b8a9-21af37513a90"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("5a39c3b6-5093-4a34-a40c-853ae2d5e26a"),
            event_id=UUID("97067d2e-7a1c-4451-ac3a-a8e974e1c6e3"),
            account_id=UUID("c12f41cd-8bd2-4c1d-896d-16e33d0df389"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("66fb561c-a0ed-4ea4-a311-fccf269b3131"),
            event_id=UUID("97067d2e-7a1c-4451-ac3a-a8e974e1c6e3"),
            account_id=UUID("bbd27b45-b5f3-4aa9-b21a-b07f5d9de9f7"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("06e2748e-9443-4e26-ae59-7f6ff747c874"),
            event_id=UUID("97067d2e-7a1c-4451-ac3a-a8e974e1c6e3"),
            account_id=UUID("a99a2fba-9fad-4650-82a7-5dfd4398b0b0"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("6785f86f-78d1-48b7-ad69-ced382497bf4"),
            event_id=UUID("ec2eb2b0-22d7-40c0-96f0-6f799227eba4"),
            account_id=UUID("886ec931-d5d4-4c66-893b-373fe5ad5a93"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("b4341e9c-8943-40a7-9080-89504b60afef"),
            event_id=UUID("ec2eb2b0-22d7-40c0-96f0-6f799227eba4"),
            account_id=UUID("bfd9708f-d51b-4fe1-bfcc-ca8cb2830a7d"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("a61713c4-9b0a-48a4-8391-5d4f6eb64357"),
            event_id=UUID("ec2eb2b0-22d7-40c0-96f0-6f799227eba4"),
            account_id=UUID("346e81a4-9470-4230-ab97-452e9dec447d"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("7fd8c901-51dc-40f2-93e9-7b5b8c10013d"),
            event_id=UUID("ec2eb2b0-22d7-40c0-96f0-6f799227eba4"),
            account_id=UUID("2fdc08c9-0264-4e1f-80ff-0625bf2e8cfe"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("9c8d48c5-654b-4629-8f68-722e5ed56837"),
            event_id=UUID("ec2eb2b0-22d7-40c0-96f0-6f799227eba4"),
            account_id=UUID("5ecbfff1-c5ba-491b-a0aa-de881b0349cb"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("e6cb5abf-fb49-4d0c-8b0a-7d6826362bbc"),
            event_id=UUID("ec2eb2b0-22d7-40c0-96f0-6f799227eba4"),
            account_id=UUID("94f35ca2-5e50-4cde-b814-37c8169c0614"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
        Ticket(
            id=UUID("0cc6905e-620d-4965-a8d2-3e2a23167d40"),
            event_id=UUID("ec2eb2b0-22d7-40c0-96f0-6f799227eba4"),
            account_id=UUID("aba1901e-ae2e-4515-9402-b25b84dcb482"),
            paid_cost=Money(amount=0, currency=Currency.CAD),
        ),
    ]

    return Dataset(
        users=users,
        addresses=addresses,
        organizations=organizations,
        organization_members=organization_members,
        venues=venues,
        events=events,
        tickets=tickets,
    )
