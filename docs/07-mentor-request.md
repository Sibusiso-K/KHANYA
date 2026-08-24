# 07-MENTOR-REQUEST — formal request for a Mintek-assigned mentor

Accompanies the abstract submission email. **Team Sonar has no mentor**, so item 5 of the
14 August 2026 letter applies: *"If you require a mentor from Mintek, please indicate this clearly
so that we can assist with the appropriate support."*

**This file is the source of truth for the wording.** [`07-mentor-request.html`](07-mentor-request.html)
is the print source and [`07-mentor-request.pdf`](07-mentor-request.pdf) is what gets sent.
Regenerate the same way as the abstract:

```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf=docs/07-mentor-request.pdf docs/07-mentor-request.html
```

`grep -a -o "/Count [0-9]*" docs/07-mentor-request.pdf` must print `/Count 1`.

---

## THE SUBMITTED LETTER

---

23 August 2026

Boitumelo Lekalakala
Mintek SCI Grad Hackathon 2026
Mintek
Private Bag X3015, Randburg 2125

**Request for a Mintek-assigned mentor — Team Sonar**

Dear Boitumelo Lekalakala,

Your letter of 14 August 2026 asks each team either to supply a mentor's name and contact details
or to indicate clearly if a mentor from Mintek is required. **Team Sonar does not have a mentor,
and we are requesting that Mintek assign one.**

We are three students at three institutions: Lethabo Hoaeane (BCom Business Informatics,
University of South Africa), Sibusiso Khumalo (BSc Electrical Engineering, University of the
Witwatersrand) and Ipeleng Modise (BSc Computer Science, Tshwane University of Technology). We
share no campus and no common supervisor, which is why we have no mentor to name.

Our entry, REEFPRINT (developed as KHANYA), addresses the *Computer Vision for Real-Time
Mineralogical Characterisation* challenge: automated identification of opaque ore minerals in
polished sections of UG2 ore, by recovering the full linear Stokes vector at every pixel from a
rotating-analyser image series. It is software, evaluated on public data; no instrument is built.

So that you can match us appropriately, the areas in which mentorship would most improve the work,
in order of value to us — any one of them would be valuable:

1. **Reflected-light ore microscopy and process mineralogy** — quantitative reflectance,
   bireflectance and anisotropy on polished sections. None of us is a practising mineralogist, and
   several of our load-bearing claims are mineralogical.
2. **UG2 and Merensky flotation, and PGE deportment** — to test whether the three operator-facing
   outputs we have chosen (fine-chromite entrainment risk, naturally-floating-gangue load for
   depressant dosing, and a stockpile oxidation index) are the ones a concentrator would act on.
3. **Automated mineralogy in practice (QEMSCAN, MLA)** — to check our characterisation of what
   SEM-based automated mineralogy does and does not deliver inside a control loop.

We are not requesting data, samples or laboratory access: we work under a self-imposed rule of
public sources only, and no proprietary Mintek data is used anywhere in this project. What we are
asking for is expert review — someone willing to tell us where we are wrong about the mineralogy,
early enough that it changes what we build.

We appreciate that mentor time is scarce. Two or three short conversations between now and
1 October would materially improve the work. We will prepare questions in advance, keep to time,
and fit whatever schedule and format suit the mentor; remote is easiest for us, and we can meet
outside working hours.

Thank you for the opportunity, and for considering this request.

Yours sincerely,

**Lethabo Hoaeane**
Team Sonar — technical lead and point of contact
Email: lethabomphukuile14@gmail.com · Mobile: 064 986 8638

On behalf of Sibusiso Khumalo and Ipeleng Modise.

---

## WORKING NOTES — NOT PART OF THE SUBMITTED LETTER

### Status: complete, no placeholders

1. ~~**Mobile number.**~~ **Filled 2026-08-23** (064 986 8638). The letter is sendable as it
   stands; the rendered PDF for attaching is `submission/Team-Sonar-mentor-request.pdf`.
2. **Check the email address.** `lethabomphukuile14@gmail.com` carries the surname *Mphukuile*,
   which we established on 2026-08-22 is not the correct surname (see `docs/BUILDLOG.md`,
   session 14). It is a perfectly ordinary thing for an address to not match a name and no
   reviewer will care — but if there is a second address that matches, use it, because this is the
   one document where the two sit two lines apart.
3. **Honorific.** The letter opens "Dear Boitumelo Lekalakala," with no title, deliberately: the
   Mintek letter gives no honorific and guessing one and getting it wrong is a worse error than
   omitting it. If the correct form of address is known, use it.

### Deliberate choices

- **The request is unambiguous and appears in the first paragraph**, in bold. Item 5 asks teams to
  "indicate this clearly"; a letter that requires reading to the end to establish whether a mentor
  is being requested has failed its only mandatory job.
- **The expertise list is the substance of the letter.** "Appropriate support" is Mintek's phrase
  and it is a matching problem — they cannot assign the right person without knowing what is
  needed. The list is ordered, and it says which single area matters most rather than asking for
  everything.
- **"None of us is a practising mineralogist" is stated plainly.** This is CLAUDE.md blind spot 8
  made into an action: *no load-bearing mineralogical claim rests on the domain lead alone; book
  external calls instead.* A mentor request is the cheapest available external check, and naming
  the gap is what makes the request matchable.
  The domain lead's prior metallurgical-engineering background is **not** claimed here — that is
  Lethabo's call to make, not a drafting decision, and the sentence is true and stronger without
  it.
- **"We are not requesting data, samples or laboratory access."** This is true (hard constraint:
  public sources only) and it removes the most likely objection to the request before it is
  raised. It also signals that we understand what we are asking for and what we are not.
- **The time ask is bounded and specific** — two or three short conversations, questions prepared
  in advance, mentor's schedule. An unbounded ask is easy to decline.
- **No claim implies an instrument exists** (ADR-0002): "It is software, evaluated on public data;
  no instrument is built."
- **One page, deliberately.** The first draft ran 46.8 mm long. It was cut by tightening prose and
  folding "any one of these would be valuable" into the list introduction — not by dropping the
  expertise list, which is the only part of the letter Mintek cannot act without. A request for
  someone's scarce time that runs to two pages is arguing against itself.

### Suggested email body this letter accompanies

> **Subject:** Team Sonar — abstract submission and request for a Mintek-assigned mentor
>
> Dear Boitumelo Lekalakala,
>
> Please find attached Team Sonar's one-page abstract for the Mintek SCI Grad Hackathon 2026,
> submitted ahead of the 30 August deadline.
>
> Also attached is a formal request for a Mintek-assigned mentor. Per item 5 of your letter of
> 14 August, we confirm that we do not currently have a mentor. The attached letter sets out the
> areas of expertise that would be most useful, so that an appropriate match can be made.
>
> Per-member details (ID number, T-shirt size and contact details) are below / attached.
>
> We have registered for the Mintek SCI Conference on 2 October 2026.
>
> Thank you,
> Lethabo Hoaeane
> Team Sonar

*(Delete the conference line if registration has not been completed yet — do not state it before
it is true.)*
