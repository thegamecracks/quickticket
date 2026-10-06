// Mock data for frontend development.
// All UUIDs, names, and relationships mirror ../mockdata.sql so the mocked
// frontend matches the seeded database exactly.
//
// Datetimes are ISO 8601 strings, as the API will return them.
// Money amounts are integers in the currency's smallest unit (cents).

import type { User, Address, Notification } from "../features/account/types"
import type { Ticket } from "../features/tickets/types"
import type { Event, Venue } from "../features/events/types"
import type { Money } from "./types"

const CAD = (amount: number): Money => ({ amount, currency: "CAD" })

// ---------------------------------------------------------------------------
// Addresses (from mockdata.sql `address`)
// ---------------------------------------------------------------------------

export const MockAddresses: Address[] = [
  {
    id: 'fdb0140f-fee0-4ffc-a0ca-1cbaaff1294e',
    account_id: 'eec50538-0edc-469b-b441-01b95b2f86c1',
    line_1: '200 Bloor St. E.',
    line_2: '',
    city: 'Whitehorse',
    province: 'Yukon',
    postal_code: 'A4K 3G1',
  },
  {
    id: '9b1554f1-e8fe-40f6-977d-6f7fef50efa9',
    account_id: '0daec970-3840-4aad-b2fb-05c1e4fa635d',
    line_1: '4201 Bank St.',
    line_2: '',
    city: 'Toronto',
    province: 'Ontario',
    postal_code: 'J9N 3V6',
  },
  {
    id: 'deed70ce-32c8-4bdf-b3a5-3722615ef91d',
    account_id: '3529c963-84c7-4e26-8017-b1805d0a4280',
    line_1: '200 Bloor St. E.',
    line_2: '',
    city: 'Victoria',
    province: 'British Columbia',
    postal_code: 'X4N 1M6',
  },
]

// ---------------------------------------------------------------------------
// Users (from mockdata.sql `account`)
// ---------------------------------------------------------------------------

/** Primary mock user: James Smith, the first account in mockdata.sql. */
export const MockUser: User = {
  id: 'eec50538-0edc-469b-b441-01b95b2f86c1',
  created_at: '2026-09-01T12:00:00.000Z',
  display_name: 'James Smith',
  first_name: 'James',
  last_name: 'Smith',
  email: 'james.smith0@example.com',
  addresses: [MockAddresses[0]],
}

/** Additional users for lists / ticket holders. */
export const MockUsers: User[] = [
  MockUser,
  {
    id: '0daec970-3840-4aad-b2fb-05c1e4fa635d',
    created_at: '2026-09-02T12:00:00.000Z',
    display_name: 'Julia Lopez',
    first_name: 'Julia',
    last_name: 'Lopez',
    email: 'julia.lopez11@example.com',
    addresses: [MockAddresses[1]],
  },
  {
    id: '3529c963-84c7-4e26-8017-b1805d0a4280',
    created_at: '2026-09-03T12:00:00.000Z',
    display_name: 'Elijah Taylor',
    first_name: 'Elijah',
    last_name: 'Taylor',
    email: 'elijah.taylor16@example.com',
    addresses: [MockAddresses[2]],
  },
]

// ---------------------------------------------------------------------------
// Organizations (from mockdata.sql `organization`)
// ---------------------------------------------------------------------------

export interface MockOrganization {
  id: string // UUID (organization_id)
  created_at: string // ISO 8601 datetime
  display_name: string
  /** account_ids of members (mockdata.sql `organization_member`). */
  member_ids: string[]
}

export const MockOrganizations: MockOrganization[] = [
  {
    id: '2cbd7222-4fd3-4cef-9500-79746e76da89',
    created_at: '2026-08-01T12:00:00.000Z',
    display_name: 'Classy Affairs',
    member_ids: ['2911b7f6-3d3f-4d03-a09e-0bfe013ef161'],
  },
  {
    id: '8e21c0af-d7a0-4f06-940c-b23728ae59e1',
    created_at: '2026-08-02T12:00:00.000Z',
    display_name: "Suzy's Event Planning and Decor",
    member_ids: ['0daec970-3840-4aad-b2fb-05c1e4fa635d'],
  },
  {
    id: '7092b056-4bec-4f3e-aec4-7f7e8f37b13d',
    created_at: '2026-08-03T12:00:00.000Z',
    display_name: 'Golden Hour Gatherings',
    member_ids: ['cd1e919c-78ac-4222-96c1-6bea98f57281', '5ecbfff1-c5ba-491b-a0aa-de881b0349cb'],
  },
  {
    id: 'f729f07d-833d-48e3-97e3-61d360b18e2e',
    created_at: '2026-08-04T12:00:00.000Z',
    display_name: 'The Grand Occasion Co.',
    member_ids: ['7ca2be93-1698-419a-9d8e-066dc81deb7c', 'aba1901e-ae2e-4515-9402-b25b84dcb482'],
  },
  {
    id: 'dbdf610b-3e5e-4565-b12a-707eb57b8b35',
    created_at: '2026-08-05T12:00:00.000Z',
    display_name: 'Evergreen Celebrations Ltd.',
    member_ids: ['54839cd2-c8fb-47ca-a9f0-fbfd73046582'],
  },
]

// ---------------------------------------------------------------------------
// Venues (from mockdata.sql `venue`)
// ---------------------------------------------------------------------------

export const MockVenues: Venue[] = [
  {
    id: '9b87e7a8-aa6b-4c60-a25b-158e1577ff25',
    organization_id: '2cbd7222-4fd3-4cef-9500-79746e76da89',
    created_at: '2026-08-10T12:00:00.000Z',
    display_name: 'Classy Affairs - Venue 1',
    description:
      '## About\nA beautiful event space featuring **floor-to-ceiling windows** and modern amenities.\n\n## Features\n- Capacity: 200 guests\n- AV equipment included\n- On-site parking\n\n## Ideal for\nWeddings, corporate events, and private parties.',
    theme: 'Banquet Hall',
    thumbnail_url: '/images/music.jpg',
    banner_url: '/images/music.jpg',
    location_name: '88 Granville St.',
    location_coords: { lat: 44.6488, long: -63.5752 },
  },
  {
    id: 'd60f59fc-721d-42bb-8a35-821de7cdc7d8',
    organization_id: '8e21c0af-d7a0-4f06-940c-b23728ae59e1',
    created_at: '2026-08-11T12:00:00.000Z',
    display_name: "Suzy's Event Planning and Decor - Venue 1",
    description:
      '## About\nA charming rustic venue with exposed brick walls and **warm lighting**.\n\n## Features\n- Capacity: 150 guests\n- Outdoor courtyard\n- Full kitchen access\n\n## Ideal for\nIntimate weddings, birthday celebrations, and small conferences.',
    theme: 'Rustic',
    thumbnail_url: '/images/art.jpg',
    banner_url: '/images/art.jpg',
    location_name: 'Sycamore Cres.',
    location_coords: null,
  },
  {
    id: 'fbacc99d-7e4c-42fb-8032-a974ff512649',
    organization_id: '8e21c0af-d7a0-4f06-940c-b23728ae59e1',
    created_at: '2026-08-12T12:00:00.000Z',
    display_name: "Suzy's Event Planning and Decor - Venue 2",
    description:
      '## About\nA state-of-the-art conference center with **flexible seating** and cutting-edge technology.\n\n## Features\n- Capacity: 500 guests\n- Breakout rooms\n- Business center\n\n## Ideal for\nConferences, product launches, and large corporate gatherings.',
    theme: 'Conference Center',
    thumbnail_url: '/images/tech.jpg',
    banner_url: '/images/tech.jpg',
    location_name: '505 Rue Laurier O.',
    location_coords: { lat: 46.8139, long: -71.208 },
  },
  {
    id: '1fb94585-3991-4d5b-817f-8aed59c3218d',
    organization_id: '7092b056-4bec-4f3e-aec4-7f7e8f37b13d',
    created_at: '2026-08-13T12:00:00.000Z',
    display_name: 'Golden Hour Gatherings - Venue 1',
    description:
      '## About\nA stunning waterfront venue offering **panoramic views** and elegant décor.\n\n## Features\n- Capacity: 300 guests\n- Outdoor terrace\n- Bridal suite\n\n## Ideal for\nWeddings, anniversary parties, and upscale dinners.',
    theme: 'Waterfront',
    thumbnail_url: '/images/jazz.jpg',
    banner_url: '/images/jazz.jpg',
    location_name: '600 Rue Saint-Jean',
    location_coords: null,
  },
  {
    id: 'a70927b2-ffa4-4c76-a79f-7f308cb1f568',
    organization_id: '7092b056-4bec-4f3e-aec4-7f7e8f37b13d',
    created_at: '2026-08-14T12:00:00.000Z',
    display_name: 'Golden Hour Gatherings - Venue 2',
    description:
      '## About\nA versatile community hall with **customizable layouts** and affordable pricing.\n\n## Features\n- Capacity: 100 guests\n- Stage available\n- Kitchen facilities\n\n## Ideal for\nCommunity events, workshops, and birthday parties.',
    theme: 'Community Hall',
    thumbnail_url: '/images/food.jpg',
    banner_url: '/images/food.jpg',
    location_name: '77 Rue du Marché Champlain',
    location_coords: null,
  },
  {
    id: '9558cd33-30bd-47b5-bbee-5360e524cd02',
    organization_id: 'f729f07d-833d-48e3-97e3-61d360b18e2e',
    created_at: '2026-08-15T12:00:00.000Z',
    display_name: 'The Grand Occasion Co. - Venue 1',
    description:
      '## About\nA beautiful event space featuring **floor-to-ceiling windows** and modern amenities.\n\n## Features\n- Capacity: 200 guests\n- AV equipment included\n- On-site parking\n\n## Ideal for\nWeddings, corporate events, and private parties.',
    theme: 'Banquet Hall',
    thumbnail_url: '/images/comedy.jpg',
    banner_url: '/images/comedy.jpg',
    location_name: '505 Rue Laurier O.',
    location_coords: { lat: 46.8139, long: -71.208 },
  },
  {
    id: 'bc96927a-7495-415f-965a-ca00ffda7fc0',
    organization_id: 'dbdf610b-3e5e-4565-b12a-707eb57b8b35',
    created_at: '2026-08-16T12:00:00.000Z',
    display_name: 'Evergreen Celebrations Ltd. - Venue 1',
    description:
      '## About\nA charming rustic venue with exposed brick walls and **warm lighting**.\n\n## Features\n- Capacity: 150 guests\n- Outdoor courtyard\n- Full kitchen access\n\n## Ideal for\nIntimate weddings, birthday celebrations, and small conferences.',
    theme: 'Rustic',
    thumbnail_url: '/images/art.jpg',
    banner_url: '/images/art.jpg',
    location_name: '888 Robson St.',
    location_coords: null,
  },
  {
    id: '820c4849-2bdc-40e5-a3df-726a091544a6',
    organization_id: 'dbdf610b-3e5e-4565-b12a-707eb57b8b35',
    created_at: '2026-08-17T12:00:00.000Z',
    display_name: 'Evergreen Celebrations Ltd. - Venue 2',
    description:
      '## About\nA state-of-the-art conference center with **flexible seating** and cutting-edge technology.\n\n## Features\n- Capacity: 500 guests\n- Breakout rooms\n- Business center\n\n## Ideal for\nConferences, product launches, and large corporate gatherings.',
    theme: 'Conference Center',
    thumbnail_url: '/images/tech.jpg',
    banner_url: '/images/tech.jpg',
    location_name: '888 Robson St.',
    location_coords: null,
  },
]

// ---------------------------------------------------------------------------
// Events (from mockdata.sql `event`)
// Dates/prices/capacities are derived from each event's markdown description
// and its venue's listed capacity.
// ---------------------------------------------------------------------------

export const MockEvents: Event[] = [
  {
    id: 'df7b2a4c-6647-43b7-88c7-17ddd2a43080',
    venue_id: '9b87e7a8-aa6b-4c60-a25b-158e1577ff25',
    created_at: '2026-09-10T12:00:00.000Z',
    display_name: 'Event 1 at Classy Affairs',
    description:
      '## Annual Gala\nJoin us for an **elegant evening** of dinner, dancing, and live entertainment.\n\n- **Date:** Saturday, March 15th\n- **Time:** 6:00 PM - 11:00 PM\n- **Dress code:** Black tie optional\n\n## Tickets\n- General Admission: $75\n- VIP Table: $500 (seats 8)',
    theme: 'Gala',
    thumbnail_url: '/images/music.jpg',
    banner_url: '/images/music.jpg',
    starts_at: '2027-03-15T18:00:00.000Z',
    ends_at: '2027-03-15T23:00:00.000Z',
    ticket_price: CAD(7500),
    max_attendees: 0,
  },
  {
    id: 'ad1d67bd-d92c-41e8-8494-c943eaaac05a',
    venue_id: '9b87e7a8-aa6b-4c60-a25b-158e1577ff25',
    created_at: '2026-09-11T12:00:00.000Z',
    display_name: 'Event 2 at Classy Affairs',
    description:
      '## Corporate Conference 2024\nA full-day conference featuring **industry leaders** and networking opportunities.\n\n- **Date:** Thursday, April 22nd\n- **Time:** 9:00 AM - 5:00 PM\n- **Lunch:** Included\n\n## Topics\n- Digital Transformation\n- Sustainable Business\n- Leadership in Uncertain Times',
    theme: 'Conference',
    thumbnail_url: '/images/tech.jpg',
    banner_url: '/images/tech.jpg',
    starts_at: '2027-04-22T09:00:00.000Z',
    ends_at: '2027-04-22T17:00:00.000Z',
    ticket_price: CAD(9900),
    max_attendees: 200,
  },
  {
    id: '0e161235-9c40-45e6-b4cd-022fd852f6e6',
    venue_id: 'd60f59fc-721d-42bb-8a35-821de7cdc7d8',
    created_at: '2026-09-12T12:00:00.000Z',
    display_name: "Event 3 at Suzy's Event Planning and Decor",
    description:
      '## Summer Wedding Expo\nDiscover the latest trends in **wedding planning**, décor, and catering.\n\n- **Date:** Saturday, June 8th\n- **Time:** 11:00 AM - 4:00 PM\n- **Admission:** Free\n\n## Features\n- Live demonstrations\n- Vendor booths\n- Fashion show',
    theme: 'Expo',
    thumbnail_url: '/images/art.jpg',
    banner_url: '/images/art.jpg',
    starts_at: '2027-06-08T11:00:00.000Z',
    ends_at: '2027-06-08T16:00:00.000Z',
    ticket_price: CAD(0),
    max_attendees: 150,
  },
  {
    id: '21afa1a9-a4ed-4d2f-8908-93b743027fec',
    venue_id: 'd60f59fc-721d-42bb-8a35-821de7cdc7d8',
    created_at: '2026-09-13T12:00:00.000Z',
    display_name: "Event 4 at Suzy's Event Planning and Decor",
    description:
      '## Charity Dinner\nAn evening dedicated to supporting **local causes** through fine dining and auctions.\n\n- **Date:** Friday, September 20th\n- **Time:** 7:00 PM - 10:00 PM\n- **Ticket Price:** $120\n\n## Proceeds benefit\n- Children\'s Hospital\n- Local Food Bank\n- Environmental Fund',
    theme: 'Charity',
    thumbnail_url: '/images/food.jpg',
    banner_url: '/images/food.jpg',
    starts_at: '2027-09-20T19:00:00.000Z',
    ends_at: '2027-09-20T22:00:00.000Z',
    ticket_price: CAD(12000),
    max_attendees: 150,
  },
  {
    id: '0c1ed79b-e063-45de-bfce-7283f5247bc3',
    venue_id: 'd60f59fc-721d-42bb-8a35-821de7cdc7d8',
    created_at: '2026-09-14T12:00:00.000Z',
    display_name: "Event 5 at Suzy's Event Planning and Decor",
    description:
      "## New Year's Eve Party\nRing in the new year with **champagne, fireworks**, and dancing until midnight.\n\n- **Date:** December 31st\n- **Time:** 9:00 PM - 2:00 AM\n- **Ticket Price:** $150\n\n## Includes\n- Open bar\n- Live DJ\n- Midnight toast",
    theme: 'Party',
    thumbnail_url: '/images/music.jpg',
    banner_url: '/images/music.jpg',
    starts_at: '2026-12-31T21:00:00.000Z',
    ends_at: '2027-01-01T02:00:00.000Z',
    ticket_price: CAD(15000),
    max_attendees: 150,
  },
  {
    id: 'ecca0ef6-390c-4b3e-9ec5-d7c307b642c5',
    venue_id: 'fbacc99d-7e4c-42fb-8032-a974ff512649',
    created_at: '2026-09-15T12:00:00.000Z',
    display_name: "Event 6 at Suzy's Event Planning and Decor",
    description:
      '## Annual Gala\nJoin us for an **elegant evening** of dinner, dancing, and live entertainment.\n\n- **Date:** Saturday, March 15th\n- **Time:** 6:00 PM - 11:00 PM\n- **Dress code:** Black tie optional\n\n## Tickets\n- General Admission: $75\n- VIP Table: $500 (seats 8)',
    theme: 'Gala',
    thumbnail_url: '/images/jazz.jpg',
    banner_url: '/images/jazz.jpg',
    starts_at: '2027-03-15T18:00:00.000Z',
    ends_at: '2027-03-15T23:00:00.000Z',
    ticket_price: CAD(7500),
    max_attendees: 500,
  },
  {
    id: '5a1231e3-8e9a-4e87-9835-6db515975d7c',
    venue_id: 'fbacc99d-7e4c-42fb-8032-a974ff512649',
    created_at: '2026-09-16T12:00:00.000Z',
    display_name: "Event 7 at Suzy's Event Planning and Decor",
    description:
      '## Corporate Conference 2024\nA full-day conference featuring **industry leaders** and networking opportunities.\n\n- **Date:** Thursday, April 22nd\n- **Time:** 9:00 AM - 5:00 PM\n- **Lunch:** Included\n\n## Topics\n- Digital Transformation\n- Sustainable Business\n- Leadership in Uncertain Times',
    theme: 'Conference',
    thumbnail_url: '/images/tech.jpg',
    banner_url: '/images/tech.jpg',
    starts_at: '2027-04-22T09:00:00.000Z',
    ends_at: '2027-04-22T17:00:00.000Z',
    ticket_price: CAD(9900),
    max_attendees: 500,
  },
  {
    id: '697102d3-6f53-4c93-b65b-f87a36a9b301',
    venue_id: '9558cd33-30bd-47b5-bbee-5360e524cd02',
    created_at: '2026-09-17T12:00:00.000Z',
    display_name: 'Event 8 at The Grand Occasion Co.',
    description:
      '## Summer Wedding Expo\nDiscover the latest trends in **wedding planning**, décor, and catering.\n\n- **Date:** Saturday, June 8th\n- **Time:** 11:00 AM - 4:00 PM\n- **Admission:** Free\n\n## Features\n- Live demonstrations\n- Vendor booths\n- Fashion show',
    theme: 'Expo',
    thumbnail_url: '/images/art.jpg',
    banner_url: '/images/art.jpg',
    starts_at: '2027-06-08T11:00:00.000Z',
    ends_at: '2027-06-08T16:00:00.000Z',
    ticket_price: CAD(0),
    max_attendees: 200,
  },
  {
    id: 'df8af935-6315-4a0f-9723-e4b031458a4d',
    venue_id: '9558cd33-30bd-47b5-bbee-5360e524cd02',
    created_at: '2026-09-18T12:00:00.000Z',
    display_name: 'Event 9 at The Grand Occasion Co.',
    description:
      '## Charity Dinner\nAn evening dedicated to supporting **local causes** through fine dining and auctions.\n\n- **Date:** Friday, September 20th\n- **Time:** 7:00 PM - 10:00 PM\n- **Ticket Price:** $120\n\n## Proceeds benefit\n- Children\'s Hospital\n- Local Food Bank\n- Environmental Fund',
    theme: 'Charity',
    thumbnail_url: '/images/food.jpg',
    banner_url: '/images/food.jpg',
    starts_at: '2027-09-20T19:00:00.000Z',
    ends_at: '2027-09-20T22:00:00.000Z',
    ticket_price: CAD(12000),
    max_attendees: 200,
  },
  {
    id: '8f691e68-a0b5-452e-9e27-4b0161dcc62a',
    venue_id: 'bc96927a-7495-415f-965a-ca00ffda7fc0',
    created_at: '2026-09-19T12:00:00.000Z',
    display_name: 'Event 10 at Evergreen Celebrations Ltd.',
    description:
      "## New Year's Eve Party\nRing in the new year with **champagne, fireworks**, and dancing until midnight.\n\n- **Date:** December 31st\n- **Time:** 9:00 PM - 2:00 AM\n- **Ticket Price:** $150\n\n## Includes\n- Open bar\n- Live DJ\n- Midnight toast",
    theme: 'Party',
    thumbnail_url: '/images/music.jpg',
    banner_url: '/images/music.jpg',
    starts_at: '2026-12-31T21:00:00.000Z',
    ends_at: '2027-01-01T02:00:00.000Z',
    ticket_price: CAD(15000),
    max_attendees: 150,
  },
  {
    id: '97067d2e-7a1c-4451-ac3a-a8e974e1c6e3',
    venue_id: '820c4849-2bdc-40e5-a3df-726a091544a6',
    created_at: '2026-09-20T12:00:00.000Z',
    display_name: 'Event 11 at Evergreen Celebrations Ltd.',
    description:
      '## Annual Gala\nJoin us for an **elegant evening** of dinner, dancing, and live entertainment.\n\n- **Date:** Saturday, March 15th\n- **Time:** 6:00 PM - 11:00 PM\n- **Dress code:** Black tie optional\n\n## Tickets\n- General Admission: $75\n- VIP Table: $500 (seats 8)',
    theme: 'Gala',
    thumbnail_url: '/images/jazz.jpg',
    banner_url: '/images/jazz.jpg',
    starts_at: '2027-03-15T18:00:00.000Z',
    ends_at: '2027-03-15T23:00:00.000Z',
    ticket_price: CAD(7500),
    max_attendees: 500,
  },
  {
    id: 'ec2eb2b0-22d7-40c0-96f0-6f799227eba4',
    venue_id: '820c4849-2bdc-40e5-a3df-726a091544a6',
    created_at: '2026-09-21T12:00:00.000Z',
    display_name: 'Event 12 at Evergreen Celebrations Ltd.',
    description:
      '## Corporate Conference 2024\nA full-day conference featuring **industry leaders** and networking opportunities.\n\n- **Date:** Thursday, April 22nd\n- **Time:** 9:00 AM - 5:00 PM\n- **Lunch:** Included\n\n## Topics\n- Digital Transformation\n- Sustainable Business\n- Leadership in Uncertain Times',
    theme: 'Conference',
    thumbnail_url: '/images/tech.jpg',
    banner_url: '/images/tech.jpg',
    starts_at: '2027-04-22T09:00:00.000Z',
    ends_at: '2027-04-22T17:00:00.000Z',
    ticket_price: CAD(9900),
    max_attendees: 500,
  },
]

// ---------------------------------------------------------------------------
// Tickets (from mockdata.sql `ticket`; ticket_ids generated since the SQL
// relies on database defaults)
// ---------------------------------------------------------------------------

export const MockTickets: Ticket[] = [
  {
    id: '1f0a3b2c-1111-4a2b-9c3d-0123456789a1',
    event_id: '0c1ed79b-e063-45de-bfce-7283f5247bc3',
    account_id: 'eec50538-0edc-469b-b441-01b95b2f86c1',
    created_at: '2026-10-01T14:30:00.000Z',
    paid_cost: CAD(40.32),
  },
  {
    id: '2b1c4d3e-2222-4b3c-8d4e-1234567890b2',
    event_id: '8f691e68-a0b5-452e-9e27-4b0161dcc62a',
    account_id: 'eec50538-0edc-469b-b441-01b95b2f86c1',
    created_at: '2026-10-02T09:15:00.000Z',
    paid_cost: CAD(18.32),
  },
  {
    id: '3c2d5e4f-3333-4c4d-9e5f-2345678901c3',
    event_id: 'ecca0ef6-390c-4b3e-9ec5-d7c307b642c5',
    account_id: 'bf90f3a5-e204-4373-acd1-dd24e1eb58f3',
    created_at: '2026-10-02T16:45:00.000Z',
    paid_cost: CAD(430),
  },
  {
    id: '4d3e6f5a-4444-4d5e-8f6a-3456789012d4',
    event_id: 'ecca0ef6-390c-4b3e-9ec5-d7c307b642c5',
    account_id: 'f9a12ff2-21ca-4ad5-b3ea-80911709726c',
    created_at: '2026-10-03T11:20:00.000Z',
    paid_cost: CAD(50.43),
  },
  {
    id: '5e4f7a6b-5555-4e6f-9a7b-4567890123e5',
    event_id: '697102d3-6f53-4c93-b65b-f87a36a9b301',
    account_id: '0837cf2f-c000-4d8c-8ec1-7aa38af5e236',
    created_at: '2026-10-03T18:05:00.000Z',
    paid_cost: CAD(0),
  },
  {
    id: '6f5a8b7c-6666-4f7a-8b8c-5678901234f6',
    event_id: '21afa1a9-a4ed-4d2f-8908-93b743027fec',
    account_id: '35c42278-c7ee-4680-b67b-65658e2438e6',
    created_at: '2026-10-04T13:40:00.000Z',
    paid_cost: CAD(12000),
  },
  {
    id: '7a6b9c8d-7777-4a8b-9c9d-6789012345a7',
    event_id: 'df8af935-6315-4a0f-9723-e4b031458a4d',
    account_id: '7ca2be93-1698-419a-9d8e-066dc81deb7c',
    created_at: '2026-10-04T20:10:00.000Z',
    paid_cost: CAD(12000),
  },
  {
    id: '8b7cad9e-8888-4b9c-8d0e-7890123456b8',
    event_id: '97067d2e-7a1c-4451-ac3a-a8e974e1c6e3',
    account_id: 'e7eb73ec-c6ac-48ca-b781-6492307a5eb2',
    created_at: '2026-10-05T10:25:00.000Z',
    paid_cost: CAD(7500),
  },
]

// ---------------------------------------------------------------------------
// Notifications (not in mockdata.sql; representative samples)
// ---------------------------------------------------------------------------

export const MockNotifications: Notification[] = [
  {
    id: '9c8dbe0f-9999-4c0d-9e1f-8901234567c9',
    account_id: 'eec50538-0edc-469b-b441-01b95b2f86c1',
    created_at: '2026-10-05T09:00:00.000Z',
    expires_at: '2026-11-05T09:00:00.000Z',
    email_at: null,
    is_read: false,
    content_short: 'Your ticket to NYE Party is confirmed!',
    content_full:
      "Your ticket to Event 5 at Suzy's Event Planning and Decor (New Year's Eve Party) has been confirmed. See you on December 31st at 9:00 PM.",
  },
  {
    id: '0d9eaf1a-0000-4d1e-8f2a-9012345678d0',
    account_id: 'eec50538-0edc-469b-b441-01b95b2f86c1',
    created_at: '2026-10-04T15:30:00.000Z',
    expires_at: '2026-11-04T15:30:00.000Z',
    email_at: '2026-10-04T16:00:00.000Z',
    is_read: true,
    content_short: 'Reminder: Annual Gala in 5 months',
    content_full: 'This is a reminder that the Annual Gala you starred begins on March 15, 2027.',
  },
]

// ---------------------------------------------------------------------------
// Lookup helpers
// ---------------------------------------------------------------------------

export const getMockEvent = (id: string) => MockEvents.find((e) => e.id === id)

export const getMockVenue = (id: string) => MockVenues.find((v) => v.id === id)

/** Tickets sold for an event (for availability = sold out vs max_attendees). */
export const getMockTicketCount = (eventId: string) =>
  MockTickets.filter((t) => t.event_id === eventId).length
