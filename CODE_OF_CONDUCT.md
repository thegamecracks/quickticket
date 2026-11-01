# Contributor Covenant Code of Conduct

- [Contributor Covenant Code of Conduct](#contributor-covenant-code-of-conduct)
  - [Our Pledge](#our-pledge)
  - [Our Standards](#our-standards)
  - [Enforcement Responsibilities](#enforcement-responsibilities)
  - [Scope](#scope)
  - [Enforcement](#enforcement)
  - [Enforcement Guidelines](#enforcement-guidelines)
    - [1. Correction](#1-correction)
    - [2. Warning](#2-warning)
    - [3. Temporary Ban](#3-temporary-ban)
    - [4. Permanent Ban](#4-permanent-ban)
  - [Attribution](#attribution)
- [AI Usage Policy](#ai-usage-policy)
  - [Details](#details)
  - [Extractive Contributions](#extractive-contributions)
  - [Handling Violations](#handling-violations)
  - [Copyright](#copyright)
  - [Examples](#examples)
  - [References](#references)

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone, regardless of age, body
size, visible or invisible disability, ethnicity, sex characteristics, gender
identity and expression, level of experience, education, socio-economic status,
nationality, personal appearance, race, religion, or sexual identity
and orientation.

We pledge to act and interact in ways that contribute to an open, welcoming,
diverse, inclusive, and healthy community.

## Our Standards

Examples of behavior that contributes to a positive environment for our
community include:

* Demonstrating empathy and kindness toward other people
* Being respectful of differing opinions, viewpoints, and experiences
* Giving and gracefully accepting constructive feedback
* Accepting responsibility and apologizing to those affected by our mistakes,
  and learning from the experience
* Focusing on what is best not just for us as individuals, but for the
  overall community

Examples of unacceptable behavior include:

* The use of sexualized language or imagery, and sexual attention or
  advances of any kind
* Trolling, insulting or derogatory comments, and personal or political attacks
* Public or private harassment
* Publishing others' private information, such as a physical or email
  address, without their explicit permission
* Other conduct which could reasonably be considered inappropriate in a
  professional setting

## Enforcement Responsibilities

Community leaders are responsible for clarifying and enforcing our standards of
acceptable behavior and will take appropriate and fair corrective action in
response to any behavior that they deem inappropriate, threatening, offensive,
or harmful.

Community leaders have the right and responsibility to remove, edit, or reject
comments, commits, code, wiki edits, issues, and other contributions that are
not aligned to this Code of Conduct, and will communicate reasons for moderation
decisions when appropriate.

## Scope

This Code of Conduct applies within all community spaces, and also applies when
an individual is officially representing the community in public spaces.
Examples of representing our community include using an official e-mail address,
posting via an official social media account, or acting as an appointed
representative at an online or offline event.

## Enforcement

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported to the community leaders responsible for enforcement at
@thegamecracks.
All complaints will be reviewed and investigated promptly and fairly.

All community leaders are obligated to respect the privacy and security of the
reporter of any incident.

## Enforcement Guidelines

Community leaders will follow these Community Impact Guidelines in determining
the consequences for any action they deem in violation of this Code of Conduct:

### 1. Correction

**Community Impact**: Use of inappropriate language or other behavior deemed
unprofessional or unwelcome in the community.

**Consequence**: A private, written warning from community leaders, providing
clarity around the nature of the violation and an explanation of why the
behavior was inappropriate. A public apology may be requested.

### 2. Warning

**Community Impact**: A violation through a single incident or series
of actions.

**Consequence**: A warning with consequences for continued behavior. No
interaction with the people involved, including unsolicited interaction with
those enforcing the Code of Conduct, for a specified period of time. This
includes avoiding interactions in community spaces as well as external channels
like social media. Violating these terms may lead to a temporary or
permanent ban.

### 3. Temporary Ban

**Community Impact**: A serious violation of community standards, including
sustained inappropriate behavior.

**Consequence**: A temporary ban from any sort of interaction or public
communication with the community for a specified period of time. No public or
private interaction with the people involved, including unsolicited interaction
with those enforcing the Code of Conduct, is allowed during this period.
Violating these terms may lead to a permanent ban.

### 4. Permanent Ban

**Community Impact**: Demonstrating a pattern of violation of community
standards, including sustained inappropriate behavior,  harassment of an
individual, or aggression toward or disparagement of classes of individuals.

**Consequence**: A permanent ban from any sort of public interaction within
the community.

## Attribution

This Code of Conduct is adapted from the [Contributor Covenant][homepage],
version 2.0, available at
https://www.contributor-covenant.org/version/2/0/code_of_conduct.html.

Community Impact Guidelines were inspired by [Mozilla's code of conduct
enforcement ladder](https://github.com/mozilla/diversity).

[homepage]: https://www.contributor-covenant.org

For answers to common questions about this code of conduct, see the FAQ at
https://www.contributor-covenant.org/faq. Translations are available at
https://www.contributor-covenant.org/translations.

# AI Usage Policy

This policy is derived from the [LLVM](https://github.com/llvm/llvm-project/blob/b3a8197fc20f1d66f35208f028e949458c922d0b/llvm/docs/AIToolPolicy.md)
project.

QuickTicket's policy is that contributors can use whatever tools they would like to
craft their contributions, but there must be a **human in the loop**.
**Contributors must read and review all LLM-generated code or text before they
ask other project members to review it.** The contributor is always the author
and is fully accountable for their contributions. Contributors should be
sufficiently confident that the contribution is high enough quality that asking
for a review is a good use of scarce maintainer time, and they should be **able
to answer questions about their work** during review.

We expect that new contributors will be less confident in their contributions,
and our guidance to them is to **start with small contributions** that they can
fully understand to build confidence. We aspire to be a welcoming community
that helps new contributors grow their expertise, but learning involves taking
small steps, getting feedback, and iterating. Passing maintainer feedback to an
LLM doesn't help anyone grow, and does not sustain our community.

Contributors are expected to **be transparent and label contributions that
contain substantial amounts of tool-generated content**. Our policy on
labelling is intended to facilitate reviews, and not to track which parts of
QuickTicket are generated. Contributors should note tool usage in their pull request
description, commit message, or wherever authorship is normally indicated for
the work. For instance, use a commit message trailer like Assisted-by: <name of
code assistant>. This transparency helps the community develop best practices
and understand the role of these new tools.

This policy includes, but is not limited to, the following kinds of
contributions:

- Code, usually in the form of a pull request
- Issues or security vulnerabilities
- Comments and feedback on pull requests

## Details

To ensure sufficient self review and understanding of the work, it is strongly
recommended that contributors write PR descriptions themselves (if needed,
using tools for translation or copy-editing). The description should explain
the motivation, implementation approach, expected impact, and any open
questions or uncertainties to the same extent as a contribution made without
tool assistance.

An important implication of this policy is that it bans agents that take action
in our digital spaces without human approval, such as the GitHub [`@claude`
agent](https://github.com/claude/). Similarly, automated review tools that
publish comments without human review are not allowed. However, an opt-in
review tool that **keeps a human in the loop** is acceptable under this policy.
As another example, using an LLM to generate documentation, which a contributor
manually reviews for correctness, edits, and then posts as a PR, is an approved
use of tools under this policy.

## Extractive Contributions

The reason for our "human-in-the-loop" contribution policy is that processing
patches, PRs, RFCs, and comments to QuickTicket is not free -- it takes a lot of
maintainer time and energy to review those contributions! Sending the
unreviewed output of an LLM to open source project maintainers *extracts* work
from them in the form of design and code review, so we call this kind of
contribution an "extractive contribution".

Our **golden rule** is that a contribution should be worth more to the project
than the time it takes to review it. These ideas are captured by this quote
from the book [Working in Public][public] by Nadia Eghbal:

[public]: https://press.stripe.com/working-in-public

> \"When attention is being appropriated, producers need to weigh the costs and
> benefits of the transaction. To assess whether the appropriation of attention
> is net-positive, it's useful to distinguish between *extractive* and
> *non-extractive* contributions. Extractive contributions are those where the
> marginal cost of reviewing and merging that contribution is greater than the
> marginal benefit to the project's producers. In the case of a code
> contribution, it might be a pull request that's too complex or unwieldy to
> review, given the potential upside.\" \-- Nadia Eghbal

Prior to the advent of LLMs, open source project maintainers would often review
any and all changes sent to the project simply because posting a change for
review was a sign of interest from a potential long-term contributor. While new
tools enable more development, it shifts effort from the implementor to the
reviewer, and our policy exists to ensure that we value and do not squander
maintainer time.

## Handling Violations

If a maintainer judges that a contribution doesn't comply with this policy,
they should paste the following response to request changes:

    This PR doesn't appear to comply with our policy on tool-generated content,
    and requires additional justification for why it is valuable enough to the
    project for us to review it. Please see our developer policy on
    AI-generated contributions: https://github.com/thegamecracks/quickticket/blob/main/CODE_OF_CONDUCT.md#handling-violations

The best ways to make a change less extractive and more valuable are to reduce
its size or complexity or to increase its usefulness to the community. These
factors are impossible to weigh objectively, and our project policy leaves this
determination up to the maintainers of the project, i.e. those who are doing
the work of sustaining the project.

If or when it becomes clear that a GitHub issue or PR is off-track and not
moving in the right direction, maintainers should apply the `extractive` label
to help other reviewers prioritize their review time.

If a contributor fails to make their change meaningfully less extractive,
maintainers should escalate to the relevant moderation or admin team for the
space (GitHub, Discourse, Discord, etc) to lock the conversation.

## Copyright

Artificial intelligence systems raise many questions around copyright that have
yet to be answered. Our policy on AI tools is similar to our copyright policy:
Contributors are responsible for ensuring that they have the right to
contribute code under the terms of our license, typically meaning that either
they, their employer, or their collaborators hold the copyright. Using AI tools
to regenerate copyrighted material does not remove the copyright, and
contributors are responsible for ensuring that such material does not appear in
their contributions. Contributions found to violate this policy will be removed
just like any other offending contribution.

## Examples

Here are some examples of contributions that demonstrate how to apply
the principles of this policy:

- [This PR][alive-pr] contains a proof from Alive2, which is a strong signal of
  value and correctness.
- This [generated documentation][gsym-docs] was reviewed for correctness by a
  human before being posted.

[alive-pr]: https://github.com/llvm/llvm-project/pull/142869
[gsym-docs]: https://discourse.llvm.org/t/searching-for-gsym-documentation/85185/2

## References

Our policy was informed by experiences in other communities:

- [Fedora Council Policy Proposal: Policy on AI-Assisted Contributions (fetched
  2025-10-01)][fedora]: Some of the text above was copied from the Fedora
  project policy proposal, which is licensed under the [Creative Commons
  Attribution 4.0 International License][cca]. This link serves as attribution.
- [Rust draft policy on burdensome PRs][rust-burdensome]
- [Seth Larson's post][security-slop]
  on slop security reports in the Python ecosystem
- The METR paper [Measuring the Impact of Early-2025 AI on Experienced
  Open-Source Developer Productivity][metr-paper].
- [QEMU bans use of AI content generators][qemu-ban]
- [Slop is the new name for unwanted AI-generated content][ai-slop]

[fedora]: https://communityblog.fedoraproject.org/council-policy-proposal-policy-on-ai-assisted-contributions/
[cca]: https://creativecommons.org/licenses/by/4.0/
[rust-burdensome]: https://github.com/rust-lang/compiler-team/issues/893
[security-slop]: https://sethmlarson.dev/slop-security-reports
[metr-paper]: https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/
[qemu-ban]: https://www.qemu.org/docs/master/devel/code-provenance.html#use-of-ai-content-generators
[ai-slop]: https://simonwillison.net/2024/May/8/slop/
