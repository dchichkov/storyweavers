from simulation import build
from runtime import solve, realize


def render(run, rng):
    entities = run["entities"]
    final = run["final"]
    events = run["events"]

    def name(entity_id):
        return entities.get(entity_id, {}).get("name", entity_id)

    def place(value):
        return {
            "library": "the library",
            "square": "the town square",
            "garden": "the reading garden",
        }.get(value, str(value))

    def after(event, key, default=None):
        change = event.get("changes", {}).get(key)
        if change is not None:
            return change.get("after", default)
        return final.get(key, default)

    def sentence_for(event):
        sid = event["scene"]

        if sid == "share_grand_sketch":
            return (
                "Mayor Bramble spread a huge sketch across a library table. "
                "“The grandest parade needs the biggest-looking cart!” he declared. "
                "Ada leaned close instead of clapping. The drawing made her curious "
                "about what the real cart could safely carry."
            )

        if sid == "inspect_balance":
            balance = after(event, "ada.knows.cart.balance", "uncertain")
            return (
                "Ada knelt beside the cart and looked carefully at how the books sat. "
                f"They had a {balance} arrangement, not quite as steady as the mayor's "
                "splendid picture suggested. “Books have centers of weight,” she "
                "murmured, tapping the floor thoughtfully."
            )

        if sid == "inspect_route":
            accessible = after(event, "ada.knows.route.square_access", False)
            answer = "open" if accessible else "not open"
            return (
                "Ada went to the library doorway and studied the route to the square. "
                f"She discovered that it was {answer}. “Now we know what the wheels "
                "will meet,” she told the others, returning with bright, practical eyes."
            )

        if sid == "measure_wheel":
            wheel = after(event, "toma.knows.cart.wheel", "unknown")
            detail = (
                "The rim was weak and needed help."
                if wheel == "weak"
                else "The rim was sound beneath his measuring fingers."
            )
            return (
                f"Toma crouched and measured the cart wheel. {detail} "
                "“A cart can be handsome and still need careful work,” he said. "
                "Ada nodded as the wheel gave a tiny squeak."
            )

        if sid == "consult_readers":
            need = after(event, "ada.knows.readers.need", 0)
            reply = (
                "Some readers needed an easier way to join."
                if need
                else "The readers said they could come to the usual gathering."
            )
            return (
                "Ada asked the readers rather than guessing what they wanted. "
                f"{reply} Mayor Bramble listened from behind a stack of atlases. "
                "His proud expression softened. “Then the sign should welcome people, "
                "not merely impress them,” he said."
            )

        if sid == "lend_cushions":
            return (
                "The keeper brought Toma a bundle of cushions. “Use these between "
                "the covers and the cart boards,” she advised. Toma accepted them "
                "with both hands. “Good protection is part of good building,” he said."
            )

        if sid == "lend_chock":
            return (
                "For the sloping stretch, the keeper lent Toma a sturdy wheel chock. "
                "Toma tested it against the floor. “This will hold the cart while we "
                "check each movement,” he explained, and tucked it beside the handle."
            )

        if sid == "lend_rope":
            return (
                "The keeper handed Ada a coil of rope. “For the tight lane,” she said. "
                "Ada ran it through her fingers and answered, “We will guide the cart "
                "slowly, not tug it wildly.” The rope became one more careful hand."
            )

        if sid == "repair_wheel":
            return (
                "Toma used the available building material to reinforce the weak wheel. "
                "He tightened, tested, and tightened again while Ada watched the rim "
                "turn. At last the squeak became a quiet roll. “It is sound now,” "
                "Toma announced, and the cart seemed to stand a little taller."
            )

        if sid == "balance_books":
            load = after(event, "cart.load", 2)
            return (
                "Ada and Toma took the books out, placed cushions between them, and "
                "rearranged the load. Heavy books went low; lighter ones rested above. "
                f"The cart now carried {load} books in a good balance, and every cover "
                "was protected. “Not biggest,” Ada said. “Ready.”"
            )

        if sid == "test_level_route":
            return (
                "Before any parade began, Ada and Toma tested the cart on the level "
                "beginning of the route. They moved it a little, stopped, listened, "
                "and checked the books. The wheels rolled smoothly. Ada grinned. "
                "“Testing tells us what imagining cannot.”"
            )

        if sid == "test_steep_route":
            return (
                "Before any parade began, Ada and Toma tested the cart on the steep "
                "stretch. Toma used the chock and called each careful step while Ada "
                "watched the books. The cart stayed steady. “Testing tells us what "
                "imagining cannot,” Ada said."
            )

        if sid == "make_invitation_sign":
            return (
                "Ada and Mayor Bramble changed the sign together. The old boast about "
                "being the “biggest” disappeared, replaced by an invitation: "
                "“Books for everyone.” Bramble held it up and smiled. “That is a "
                "promise I can be proud of,” he said."
            )

        if sid == "guide_open_square_route":
            return (
                "The group guided the balanced cart along the open route. Toma watched "
                "the wheels, Ada watched the books, and Bramble watched faces turning "
                "toward the invitation. When they reached the square, every book was "
                "still safe and ready to be opened."
            )

        if sid == "guide_narrow_square_route":
            return (
                "The lane was narrow, so Ada held the rope while Toma guided the handle "
                "and Bramble cleared the way. “A little left—now pause!” Ada called. "
                "The cart slipped neatly between the walls and emerged at the square "
                "without a single book sliding loose."
            )

        if sid == "guide_garden_route":
            return (
                "The group chose the reachable reading garden instead of forcing an "
                "unsuitable route. The cart rolled to a welcoming patch of shade, "
                "where books could be displayed and readers could gather. Bramble "
                "looked at the sign and said, “A parade can travel by serving its "
                "readers.”"
            )

        return event["summary"] + "."

    paragraphs = [{
        "text": (
            "In the little town library, Mayor Bramble wanted a parade that looked "
            "enormous. Ada, who noticed loose wheels and lopsided books, wondered "
            "whether a grand parade might be measured another way. Toma, the careful "
            "cart builder, was ready to inspect every useful detail. Together they "
            "would discover what the cart, the route, and the readers actually needed."
        ),
        "event_ids": [],
        "kind": "beginning",
    }]

    for event in events[:-1]:
        paragraphs.append({
            "text": sentence_for(event),
            "event_ids": [event["id"]],
            "kind": "scene",
        })

    if events:
        last = events[-1]
        location = final.get("parade.location", "library")
        kind = final.get("parade.kind", "reading gathering")
        paragraphs.append({
            "text": (
                sentence_for(last)
                + f" At {place(location)}, the finished arrangement was a {kind}. "
                "The cart stood steady, its protected books displayed where people "
                "could reach them. Mayor Bramble touched the new sign and laughed "
                "softly. Ada opened the first book, Toma settled the cart, and the "
                "very first reader leaned in."
            ),
            "event_ids": [last["id"]],
            "kind": "ending",
        })
    else:
        paragraphs.append({
            "text": "The library stayed quiet, with the cart waiting for another try.",
            "event_ids": [],
            "kind": "ending",
        })

    return paragraphs


def generate(seed, prose_seed=None):
    return realize(
        solve(build(seed), seed),
        render,
        seed if prose_seed is None else prose_seed,
    )
