#!/usr/bin/env python3
"""
A heartwarming tiny storyworld about a parade, a sailor, infantry, and a twist.

The world is built for a small, child-friendly tale:
- A sailor and an infantry squad help prepare a parade.
- A problem in the middle creates tension.
- A twist reveals that the most helpful choice is to support someone else.
- The ending proves the change with a warm, shared image.

The script supports prose generation, QA, JSON, trace output, and a small ASP twin.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
sys.path.insert(0, os.path.dirname(_storyworlds_dir))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    sailor: str = "Mara"
    infantry_lead: str = "Ben"
    parade_place: str = "the town square"
    item: str = "a bright banner"
    seed: Optional[int] = None
    arc: int = 0


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    sailor: Entity
    infantry_lead: Entity
    band: Entity
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SAILORS = ["Mara", "June", "Iris", "Nico", "Lena", "Toby", "Sage", "Owen"]
INFANTRY = ["Ben", "Ada", "Hugo", "Mina", "Levi", "Noa", "Ruth", "Jasper"]
PLACES = ["the town square", "the harbor road", "the school yard", "the festival gate"]
ITEMS = [
    "a bright banner",
    "a ribboned drum",
    "a parade wreath",
    "a brass whistle",
    "a bundle of flags",
]

ARCS = [
    {
        "premise": "The sailor was helping the infantry line up for the spring parade",
        "problem": "a wind gust snatched the lead banner and tangled it on a gatepost",
        "stake": "without the banner, the parade would begin in a messy, sad way",
        "temptation": "rush ahead alone and pull the banner free before anyone noticed",
        "clue": "the infantry boots had already packed the mud into a firm little path",
        "action": "they asked the squad to hold the ropes while the sailor climbed carefully and loosened the knot",
        "twist": "the snagged banner had actually kept a tiny kitten from wandering into the road",
        "sharing": "everyone took turns carrying the kitten, and the parade formed around it like a safe circle",
        "lesson": "helping together can turn a mistake into a kindness",
        "ending": "the kitten rode in a soft satchel while the banner waved above a smiling parade",
        "question": "Why did the parade need the banner?",
        "answer": "The parade needed the banner so the march could begin in a neat and cheerful way.",
    },
    {
        "premise": "The sailor and the infantry were decorating the parade route with paper stars",
        "problem": "rain wet the glue and the stars kept slipping from the lamp posts",
        "stake": "the street would look plain if the decorations all fell",
        "temptation": "climb fast and tape up only the biggest stars for a grand show",
        "clue": "the infantry's canteen cups still held dry paper scraps from lunch",
        "action": "they made small paper pockets, one for each star, and tucked them under the lamps",
        "twist": "the plainest paper scraps spelled out thank-you notes from the children",
        "sharing": "they pinned the notes beside the stars so everyone in the parade could read them",
        "lesson": "little shared comforts can brighten a rainy day",
        "ending": "wet sidewalks glittered under stars and thank-you notes, and the marchers grinned through the drizzle",
        "question": "What problem did the rain cause?",
        "answer": "The rain made the glue slippery, so the paper stars kept falling from the lamp posts.",
    },
    {
        "premise": "The sailor brought a small drum to help the infantry keep time",
        "problem": "the drumstick snapped just as the parade captain called for the first beat",
        "stake": "without a steady rhythm, the marching lines would drift apart",
        "temptation": "borrow the captain's polished baton and pretend it was good enough",
        "clue": "one infantry child was tapping the same beat on a metal cup",
        "action": "they wrapped cloth around the cup, shared the tapping pattern, and marched to a softer rhythm",
        "twist": "the softer rhythm matched the babies in the crowd, and even the quietest listeners started to clap",
        "sharing": "the sailor gave the drum to the infantry child who heard the beat best",
        "lesson": "a gentle rhythm can bring more hearts along than a loud one",
        "ending": "the parade moved like one warm line, with the cup-beat leading smiles down the road",
        "question": "What replaced the broken drumstick's beat?",
        "answer": "A soft tapping pattern on a metal cup replaced the broken drumstick's beat.",
    },
    {
        "premise": "The sailor was polishing the parade medals for the infantry honor march",
        "problem": "one medal slipped into a puddle and sank under muddy water",
        "stake": "the honored recruit would have no medal to wear in front of the crowd",
        "temptation": "jump into the puddle alone and search until the boots filled with mud",
        "clue": "the medal had left a small sparkle trail on the water's surface",
        "action": "they asked the infantry to ring a circle of lanterns and watched where the sparkle moved",
        "twist": "the medal had not sunk at all; a frog had borrowed it and sat wearing it like a crown",
        "sharing": "the frog hopped onto the soldier's cap for the parade, and the medal was shared as a joke and a cheer",
        "lesson": "sometimes the funniest answer is also the kindest one",
        "ending": "the frog bowed from a cap-brim while the crowd laughed softly and clapped together",
        "question": "Where did the missing medal go?",
        "answer": "A frog had picked up the medal and was wearing it like a tiny crown.",
    },
    {
        "premise": "The infantry were carrying a long parade arch to the station gate",
        "problem": "the arch tipped and blocked a child pulling a cart of oranges",
        "stake": "the parade line could not move until the path was clear",
        "temptation": "tell the child to wait and keep the arch balanced by force",
        "clue": "the sailor noticed the cart wheels fit exactly inside the arch's lower curve",
        "action": "they lifted together, slid the cart through first, and then set the arch over the route",
        "twist": "the oranges had been meant for the parade volunteers, and the child had been searching for them",
        "sharing": "everyone shared the oranges, and the child helped place the last ribbon",
        "lesson": "a crowd can be kinder when it makes room before it asks for applause",
        "ending": "the arch stood bright over a line of sticky-fingered marchers and a very happy cart driver",
        "question": "How did the sailor and infantry clear the path?",
        "answer": "They lifted the arch together and slid the child and cart safely through first.",
    },
    {
        "premise": "A small parade float with painted birds was waiting near the quay",
        "problem": "its wheel had sunk into soft ground and would not roll",
        "stake": "the float would miss the front of the parade and disappoint the children",
        "temptation": "push hardest on the strongest wheel and leave the others behind",
        "clue": "the infantry noticed the soft ground was firm where the sailor had already walked",
        "action": "they laid planks in a shared line and rolled the float along the stronger path",
        "twist": "the painted birds looked so real that a flock landed on the float for a moment",
        "sharing": "the sailor and infantry kept still so the birds could rest before the parade moved on",
        "lesson": "patience can invite a blessing that hurry would scare away",
        "ending": "birds lifted from the float like confetti, and the children cheered as it rolled free",
        "question": "Why could the float move after the planks were laid?",
        "answer": "The planks made a firm path over the soft ground, so the wheel could roll again.",
    },
    {
        "premise": "The sailor was teaching the infantry how to wave at the crowd",
        "problem": "one shy recruit hid behind a drum and would not step forward",
        "stake": "the recruit would miss the chance to march in the front row",
        "temptation": "give the recruit a stern push and demand a loud wave",
        "clue": "the sailor saw that the recruit smiled whenever someone else waved first",
        "action": "they began with tiny waves, then passed a glove from hand to hand until the recruit joined in",
        "twist": "the shy recruit knew every face in the crowd and had been saving spots for lost children",
        "sharing": "the recruit led the children to their families, and the wave became a welcome for everyone",
        "lesson": "quiet kindness can be the bravest part of a parade",
        "ending": "the shy recruit waved from the center of the line, and the whole square waved back",
        "question": "What helped the shy recruit start waving?",
        "answer": "Tiny waves from others and the shared glove helped the recruit feel brave enough to join in.",
    },
    {
        "premise": "The sailor brought a kite to fly above the infantry parade",
        "problem": "the kite string tangled around a sign and the parade crowd stopped",
        "stake": "the banner bearer could not move until the string was untied",
        "temptation": "pull hard and tear the string to save time",
        "clue": "the infantry noticed the string had slipped through two neat loops, like a bow",
        "action": "they loosened the loops together and let the sailor guide the kite into open air",
        "twist": "the kite had been carrying a note from the mayor asking the children to lead the final march",
        "sharing": "the sailor handed the kite tail to the children, and they ran ahead laughing",
        "lesson": "a surprise can become a gift when it is shared on purpose",
        "ending": "the kite floated above marching feet while the children took the front in bright, proud steps",
        "question": "What was hidden on the kite?",
        "answer": "The kite carried a note from the mayor asking the children to lead the final march.",
    },
]

OPENINGS = [
    "Morning bells rang softly over the square",
    "A warm breeze stirred the flags before the first drumbeat",
    "Sunlight touched the parade route and made the brass shine",
    "The harbor air smelled like salt, paint, and fresh bread",
    "Before noon, the whole town seemed to gather its breath",
    "The street was bright enough to feel like a promise",
]

THOUGHTS = [
    "'If I hurry alone, I may miss the kinder way; if I pause and ask, we may save the day.'",
    "'A parade should not begin with panic and fear; one careful shared step may make everything clear.'",
    "'I want to be helpful, but not by myself; the best plan is one we can place on the shelf.'",
    "'A quick fix may shine, but a gentle one lasts; I should listen before I rush past.'",
]

TWIST_REACTIONS = [
    "{infantry} laughed in relief",
    "{infantry} blinked, then smiled wide",
    "The crowd gasped, then softened into laughter",
    "{infantry} put a hand over their heart",
    "{infantry} gave a surprised little cheer",
]

CLOSINGS = [
    "By the end, the parade looked brighter because everyone had helped someone else.",
    "When the last march finished, the town felt warmer than before.",
    "The best part of the day was not the noise, but the shared kindness in it.",
    "Everyone went home with cleaner hands, lighter hearts, and one sweet story to remember.",
    "The parade ended as it should: with smiles that belonged to many people at once.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming storyworld about a parade, a sailor, and infantry.")
    ap.add_argument("--sailor", choices=SAILORS)
    ap.add_argument("--infantry", choices=INFANTRY)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    sailor = args.sailor or rng.choice(SAILORS)
    infantry_lead = args.infantry or rng.choice([n for n in INFANTRY if n != sailor])
    if sailor == infantry_lead:
        raise StoryError("The sailor and infantry lead must be different characters.")
    return StoryParams(
        sailor=sailor,
        infantry_lead=infantry_lead,
        parade_place=args.place or rng.choice(PLACES),
        item=args.item or rng.choice(ITEMS),
        seed=args.seed,
        arc=rng.randrange(len(ARCS)),
    )


def build_world(params: StoryParams) -> World:
    return World(
        params=params,
        sailor=Entity(name=params.sailor, kind="sailor"),
        infantry_lead=Entity(name=params.infantry_lead, kind="infantry"),
        band=Entity(name="parade band", kind="group"),
    )


def choose(rng: random.Random, options: list[str], **values: str) -> str:
    return rng.choice(options).format(**values)


def simulate(world: World) -> None:
    p = world.params
    arc = ARCS[p.arc]
    rng = random.Random(p.seed or 0)
    sailor = world.sailor
    infantry = world.infantry_lead

    sailor.meters["confidence"] = 1.0
    infantry.meters["readiness"] = 1.0
    sailor.memes["kindness"] = 1.0
    infantry.memes["trust"] = 1.0

    world.facts["place"] = p.parade_place
    world.facts["item"] = p.item
    world.facts["problem"] = arc["problem"]
    world.facts["twist"] = arc["twist"]

    opening = choose(rng, OPENINGS, sailor=sailor.name, infantry=infantry.name)
    world.say(
        f"{opening}. In {p.parade_place}, {sailor.name} the sailor joined {infantry.name} and the infantry team "
        f"to prepare {p.item} for the parade."
    )
    world.say(f"{arc['premise']}. The air was busy, but friendly, and everyone wanted the day to go well.")
    world.para()

    world.say(f"Then {arc['problem']}. {arc['stake']}.")
    world.say(f"{sailor.name} felt a fast, brave urge to {arc['temptation']}.")
    world.say("But the thought of making a mess in front of the children made that idea feel too sharp.")
    world.say(f"{sailor.name} thought, {choose(rng, THOUGHTS, sailor=sailor.name, infantry=infantry.name)}")
    sailor.memes["hesitation"] = 1.0

    world.para()
    world.say(
        f"{infantry.name} noticed a clue: {arc['clue']}. "
        f"So {sailor.name} and {infantry.name} asked the others to help."
    )
    world.say(f"{arc['action']}.")
    world.say(f"Then came the twist: {arc['twist']}. {choose(rng, TWIST_REACTIONS, sailor=sailor.name, infantry=infantry.name)}.")
    sailor.memes["surprise"] = 1.0
    sailor.memes["sharing"] = 1.0
    infantry.memes["sharing"] = 1.0
    world.facts["solution"] = arc["action"]
    world.facts["twist_reveal"] = arc["twist"]

    world.para()
    world.say(f"After that, {arc['sharing']}.")
    world.say(f"{sailor.name} smiled and said, “We did better when we did it together.”")
    world.say(f"{infantry.name} answered, “And now the parade can shine for everyone.”")
    world.say(f"{choose(rng, CLOSINGS)} {arc['ending']}.")
    sailor.meters["confidence"] = 2.0
    infantry.meters["readiness"] = 2.0
    sailor.memes["joy"] = 2.0
    infantry.memes["joy"] = 2.0
    world.facts["resolved"] = True
    world.facts["ending_image"] = arc["ending"]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    arc = ARCS[params.arc]
    prompts = [
        f"Write a heartwarming story about {params.sailor}, {params.infantry_lead}, and a parade at {params.parade_place}.",
        f"Tell a child-friendly tale where the sailor and infantry face this problem: {arc['problem']}.",
        f"Include a twist and a warm ending using {params.item}.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.sailor} first want to do when trouble started?",
            answer=f"{params.sailor} first wanted to {arc['temptation']}.",
        ),
        QAItem(
            question=f"What clue helped {params.sailor} and {params.infantry_lead} solve the problem?",
            answer=f"The clue was that {arc['clue']}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {arc['twist']}.",
        ),
        QAItem(
            question="How did the characters help each other in the end?",
            answer=f"They worked together: {arc['action']}.",
        ),
        QAItem(
            question="What did the story show about kindness?",
            answer=f"It showed that {arc['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a parade?",
            answer="A parade is a cheerful public march where people walk together to celebrate something.",
        ),
        QAItem(
            question="What is an infantry?",
            answer="Infantry are soldiers who move and work on foot.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works on a boat or ship and knows the water.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.sailor, world.infantry_lead, world.band]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.name:12} ({ent.kind:8}) meters={meters} memes={memes}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/1.
valid(story) :- parade(place), sailor(X), infantry(Y), X != Y, twist_feature.
twist_feature :- feature(twist).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("domain", "parade"),
            asp.fact("domain", "sailor"),
            asp.fact("domain", "infantry"),
            asp.fact("feature", "twist"),
            asp.fact("style", "heartwarming"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/1."))
    if asp.atoms(model, "valid") == [("story",)]:
        print("OK: ASP twin is consistent.")
        return 0
    print("MISMATCH: ASP twin failed.")
    return 1


CURATED = [
    StoryParams(sailor="Mara", infantry_lead="Ben", parade_place="the town square", item="a bright banner", seed=101, arc=0),
    StoryParams(sailor="June", infantry_lead="Hugo", parade_place="the harbor road", item="a parade wreath", seed=202, arc=2),
    StoryParams(sailor="Lena", infantry_lead="Mina", parade_place="the festival gate", item="a bundle of flags", seed=303, arc=6),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/1."))
        print(asp.atoms(model, "valid"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            if params.seed is None:
                params.seed = base_seed + i
            sample = generate(params)
            i += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
