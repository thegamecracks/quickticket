# QuickTicket

QuickTicket is a ticket sales platform for small and medium-scale events:
organizers publish events at their venues, and attendees obtain tickets to
attend them.

## Language

### People and roles

**User**:
A person with a QuickTicket account, who acts as an attendee, an organizer, an
administrator, or some combination of them.
_Avoid_: Account, customer, guest, member

**Attendee**:
The user role for people who attend events by obtaining tickets to them.
_Avoid_: Guest, customer, ticket holder, registrant

**Organizer**:
The user role for people who own or co-own an organization and create its
venues and events.
_Avoid_: Host, admin, manager, organization administrator

**Administrator**:
The user role for people who manage the whole system and moderate its content.
Not yet available.
_Avoid_: Admin, owner, host, organization administrator

**Organization**:
A group, represented by one or more organizers, that owns venues and the events
held there.
_Avoid_: Host, organizer, team, business

**Organization member**:
A user who belongs to an organization, carrying the permissions that user has
within it.
_Avoid_: Staff, admin, member account

### Events

**Venue**:
A place where an organization holds events, presented publicly under its own
name, description, category, and images. A venue without coordinates is
virtual.
_Avoid_: Location, space, place

**Event**:
A single scheduled happening at one venue, with a start and end time, a
category, a ticket price, and a capacity.
_Avoid_: Show, occurrence, session, series

**Category**:
The category an event or venue is filed under, such as Music, Comedy, or Food.
Categories are an open vocabulary, not a fixed list.
_Avoid_: Theme (reserved for visual styling), genre, tag

### Tickets and money

**Ticket**:
One person's admission to one event. An attendee may hold several tickets to
the same event and pass them to people without a QuickTicket account.
_Avoid_: Registration, RSVP, booking, order, pass

**Ticket price**:
The price of one ticket to an event.
_Avoid_: Admission fee, cost

**Paid cost**:
What was actually paid for a ticket.
_Avoid_: Price, total, charge

**Capacity**:
The maximum number of attendees an event admits. A capacity of zero admits no
one.
_Avoid_: Max attendees, limit, seats

**Money**:
An amount paired with the currency it is charged in, held as an integer in that
currency's smallest unit.
_Avoid_: Price, total, amount

**Currency**:
The currency that will be charged, named as Stripe names it, such as Canadian
dollars or Japanese Yen.
_Avoid_: Denomination, money type

### Communication

**Notification**:
A message addressed to one user, which that user can mark as read.
_Avoid_: Alert, message, email

**Announcement**:
A message from an organization about one of its events, delivered to that
event's attendees as notifications.
_Avoid_: Update, broadcast, notification

### Identity

**OpenID account**:
A user's identity at an external OpenID provider, linked to exactly one user.
Written as one term so it is never mistaken for a QuickTicket account.
_Avoid_: Login, SSO account, identity, profile
