# QuickTicket

[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/quickticket/backend-test.yml?style=flat-square&logo=django&label=backend)](https://github.com/thegamecracks/quickticket/actions/workflows/backend-test.yml)
[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/quickticket/zizmor.yml?style=flat-square&label=zizmor)](https://github.com/thegamecracks/quickticket/actions/workflows/zizmor.yml)

## Summary

QuickTicket is a web-based ticket sales platform for small and medium-scale events.
It allows unaffiliated organizers of small-scale venues to set up public or invite-only
events in minutes.

Attendees can browse and search through events, register themselves through email
verification, single sign-on, or a guest flow, and receive tickets for free or
purchase tickets, based on the event type. Tickets are saved on the platform and
e-mailed to the customer as proof of registration.

The purchasing of tickets will be simulated during development but will have the
capability to swap in a live payment processor. Attendees will be able to receive
updates from the host of any given event to be notified of any event changes such
as weather warnings, delays, and cancellations.

## Architecture

![Initial architecture diagram](/docs/images/initial_architecture.png)
