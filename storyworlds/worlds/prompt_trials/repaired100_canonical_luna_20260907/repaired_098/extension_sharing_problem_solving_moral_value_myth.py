#!/usr/bin/env python3
"""A child-facing myth about an extension, sharing, and clever problem solving."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Being:
    name: str
    kind: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str = "mythic place"
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Gift:
    name: str
    material: str
    owner: str
    shared: bool = False
    useful: bool = False


@dataclass(frozen=True)
class MythCase:
    need: str
    danger: str
    first_idea: str
    failed_reason: str
    clue: str
    solution: str
    sharing_action: str
    moral: str
    ending: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    valley_name: str = "the Valley of Seven Hills"
    hero_name: str = "Luna"
    hero_kind: str = "moon-weaver"
    elder_name: str = "Tavi"
    elder_kind: str = "turtle"
    gift_name: str = "the silver extension"
    gift_material: str = "moon-thread"
    case: str = "moon_bridge"
    route: str = "old_song"


@dataclass
class World:
    valley: Place
    hero: Being
    elder: Being
    gift: Gift
    case: MythCase
    solved: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


CASES = {
    "moon_bridge": MythCase(
        need="the children of the far hill could not cross the dark stream to join the moon feast",
        danger="the rushing water could sweep a small traveler away",
        first_idea="tied a single shining ribbon from one bank to the other",
        failed_reason="the ribbon reached only halfway and snapped when the wind pulled it",
        clue="three old willow roots reached toward one another beneath the water",
        solution="the willow roots could hold a careful chain of braided moon-thread",
        sharing_action="unrolled the silver extension and invited every family to add one strong strand",
        moral="a gift grows greater when many hands are trusted to use it",
        ending="the new moon bridge glowed across the stream, and every child reached the feast safely",
    ),
    "sun_ladder": MythCase(
        need="the village garden had no light because a tall cloud covered the sunstone",
        danger="climbing the slippery cloud-rock alone could cause a fall",
        first_idea="built a ladder from six short reeds",
        failed_reason="the reeds bent before they reached the sunstone",
        clue="the beavers had stored long willow poles beside the shared pond",
        solution="the willow poles could extend the ladder while the pond keepers held its feet",
        sharing_action="opened the storehouse and let each neighbor lend a pole",
        moral="a problem becomes smaller when useful things are shared with care",
        ending="the extended ladder touched the sunstone, and warm light returned to every garden",
    ),
    "rain_song": MythCase(
        need="the rain drum could not be heard by the thirsty orchards beyond the ridge",
        danger="carrying the heavy drum over the ridge could exhaust one traveler",
        first_idea="rolled the drum alone toward the high path",
        failed_reason="it stopped whenever the stones grew steep",
        clue="old copper pipes lay in a line beneath the singing grass",
        solution="the pipes could extend the drum's voice from the ridge to the orchards",
        sharing_action="asked each orchard keeper to lend a pipe and a listening ear",
        moral="wisdom is not keeping a good answer hidden from those who need it",
        ending="the rain song traveled through the joined pipes, and the first drops filled every orchard bowl",
    ),
    "star_rope": MythCase(
        need="the shepherds could not find the lost star-lamb beyond the mist field",
        danger="entering the mist without a guide could make a traveler lose the path",
        first_idea="shouted the lamb's name from the field gate",
        failed_reason="the mist swallowed the sound before it reached the far stones",
        clue="a line of bright seeds marked the old shepherds' route",
        solution="the seeds could extend a safe trail when tied to the silver cord",
        sharing_action="gave the cord to the shepherds and let each person hold part of the trail",
        moral="a safe path belongs to everyone who walks it together",
        ending="the silver trail led the lamb home, and the mist opened like a curtain",
    ),
}

CASES_LIST = [
    ("moon_bridge", "the moon bridge needed an extension", "moon-thread"),
    ("sun_ladder", "the sun ladder needed an extension", "willow"),
    ("rain_song", "the rain song needed an extension", "copper"),
    ("star_rope", "the star rope needed an extension", "silver"),
]

HEROES = [("Luna", "moon-weaver"), ("Neri", "cloud-child"), ("Mara", "river-keeper")]
ELDERS = [("Tavi", "turtle"), ("Oren", "raven"), ("Sela", "old fox")]
ROUTES = ("old_song", "village_call", "strange_clue", "twilight", "question_first")


ASP_RULES = r"""
valid_need(N) :- need(N).
extended(G) :- gift(G), shared(G), useful(G).
solved(C) :- case(C), valid_need(C), extended(extension).
valid_story(C) :- solved(C), moral_value(sharing).
"""


def safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("gift", "extension"),
        asp.fact("shared", "extension"),
        asp.fact("useful", "extension"),
        asp.fact("moral_value", "sharing"),
    ]
    for key, _, _ in CASES_LIST:
        lines.append(asp.fact("case", key))
        lines.append(asp.fact("need", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    actual = set(asp.atoms(model, "solved"))
    expected = {(key,) for key, _, _ in CASES_LIST}
    if actual == expected:
        print(f"OK: clingo gate matches python reasoning ({len(expected)} myths).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(actual))
    print("python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(v) for v in (
        params.seed, params.valley_name, params.hero_name, params.hero_kind,
        params.elder_name, params.elder_kind, params.case, params.route,
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.case not in CASES:
        raise StoryError(f"Unknown myth case: {params.case}")
    if not params.hero_name.strip():
        raise StoryError("Hero name cannot be empty.")
    if not params.elder_name.strip():
        raise StoryError("Elder name cannot be empty.")
    case = CASES[params.case]
    return World(
        valley=Place(params.valley_name, "mythic valley"),
        hero=Being(params.hero_name, params.hero_kind, "solver"),
        elder=Being(params.elder_name, params.elder_kind, "wise helper"),
        gift=Gift(params.gift_name, params.gift_material, params.hero_name),
        case=case,
    )


def tell_story(world: World, params: StoryParams) -> None:
    rng = story_rng(params)
    h, e, place, gift, case = world.hero, world.elder, world.valley, world.gift, world.case
    h.memes.update(curiosity=1.0, generosity=0.0, courage=0.0)
    e.memes.update(wisdom=1.0, patience=1.0)

    openings = {
        "old_song": (
            f"Long ago, when the moon still whispered names to the hills, {h.name} lived in {place.name}. "
            f"One evening, {case.need}."
        ),
        "village_call": (
            f'"Who will help us?" called the people of {place.name}. {case.need.capitalize()}.' 
            f" {h.name}, a young {h.kind}, heard them from the moonlit path."
        ),
        "strange_clue": (
            f"A silver thread appeared beside the oldest stone in {place.name}. "
            f"{h.name} followed it and learned that {case.need}."
        ),
        "twilight": (
            f"At twilight, the moon painted {place.name} blue. Then everyone discovered that {case.need}."
            f" {h.name} carried {gift.name}, hoping it might help."
        ),
        "question_first": (
            f'"How can one small extension reach a place so far away?" {h.name} asked. '
            f"The question mattered because {case.need}."
        ),
    }
    world.say(openings[params.route])
    world.say(f"The danger was real: {case.danger}.")
    world.say(rng.choice([
        f'{e.name}, a wise {e.kind}, arrived and said, "A brave heart does not have to solve a wide problem alone."',
        f'"Tell me what you know," {e.name} said. {h.name} showed the silver extension instead of hiding it.',
        f'{e.name} touched the ground and answered, "Before we act, let us learn what the place is already telling us."',
    ]))

    world.para()
    world.say(f"First, {h.name} {case.first_idea}.")
    world.say(rng.choice([
        f"But the plan failed because {case.failed_reason}.",
        f"The attempt looked bright, yet {case.failed_reason}.",
        f'"That is not enough," {h.name} admitted, for {case.failed_reason}.',
    ]))
    world.say(rng.choice([
        f"Then {e.name} noticed that {case.clue}.",
        f"An old song helped them see the clue: {case.clue}.",
        f"Instead of blaming the failed plan, they searched again and found that {case.clue}.",
    ]))
    world.say(f"The answer became clear: {case.solution}.")

    world.para()
    world.say(f"{h.name} held {gift.name} close, then chose to {case.sharing_action}.")
    h.memes["generosity"] = 1.0
    h.memes["courage"] = 1.0
    gift.shared = True
    gift.useful = True
    world.say(rng.choice([
        f'"The extension is not smaller when we share it," {h.name} said. "It reaches farther."',
        f'{e.name} smiled. "A clever answer is a lantern. Its light is meant to travel."',
        f"Together they measured, tied, listened, and tested until the joined material held firm.",
    ]))
    world.solved = True
    world.facts.update(
        need=case.need,
        danger=case.danger,
        failed_reason=case.failed_reason,
        clue=case.clue,
        solution=case.solution,
        sharing_action=case.sharing_action,
        moral=case.moral,
        ending=case.ending,
    )

    world.para()
    world.say(rng.choice([
        f"The people remembered this moral: {case.moral}.",
        f'{e.name} taught the children, "Remember: {case.moral}."',
        f"{h.name} understood that the true magic was not the material but the choice to share it. {case.moral.capitalize()}.",
    ]))
    world.say(rng.choice([
        f"By moonrise, {case.ending}.",
        f"And from that night onward, {case.ending}.",
        f"The change could be seen from every hill: {case.ending}.",
    ]))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-facing myth about {world.hero.name} using an extension to solve this need: {f['need']}.",
        f"Show how sharing helps solve the problem: {f['sharing_action']}.",
        f"End with this mythic image: {f['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, e, gift, case = world.hero, world.elder, world.gift, world.case
    return [
        QAItem(
            question=f"What problem did {h.name} try to solve?",
            answer=f"{h.name} tried to solve the problem that {case.need}. It was dangerous because {case.danger}.",
        ),
        QAItem(
            question=f"Why did {h.name}'s first idea fail?",
            answer=f"{h.name} first {case.first_idea}, but that failed because {case.failed_reason}.",
        ),
        QAItem(
            question=f"What clue helped {h.name} discover the solution?",
            answer=f"The important clue was that {case.clue}. This showed that {case.solution}.",
        ),
        QAItem(
            question=f"How did sharing help solve the problem?",
            answer=f"{h.name} chose to {case.sharing_action}. Sharing made the extension reach the place that needed help.",
        ),
        QAItem(
            question="What moral value does the myth teach?",
            answer=f"The myth teaches that {case.moral}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an extension?",
            answer="An extension is something added to make a tool, path, sound, or reach go farther.",
        ),
        QAItem(
            question="Why can sharing help with problem solving?",
            answer="Sharing lets people combine useful materials, ideas, and effort instead of trying to solve a large problem alone.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is a traditional-style story that uses memorable characters and wonder to explore important truths or values.",
        ),
        QAItem(
            question="What does generosity mean?",
            answer="Generosity means willingly giving help, time, ideas, or useful things to benefit others.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth about an extension, sharing, and problem solving.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--valley")
    ap.add_argument("--hero-name")
    ap.add_argument("--elder-name")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    case, _, material = rng.choice(CASES_LIST)
    hero_name, hero_kind = rng.choice(HEROES)
    elder_name, elder_kind = rng.choice(ELDERS)
    return StoryParams(
        seed=args.seed,
        valley_name=args.valley or rng.choice([
            "the Valley of Seven Hills",
            "the Valley Beneath the Moon",
            "the Valley of Singing Stones",
        ]),
        hero_name=args.hero_name or hero_name,
        hero_kind=hero_kind,
        elder_name=args.elder_name or elder_name,
        elder_kind=elder_kind,
        gift_name="the silver extension",
        gift_material=material,
        case=case,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world trace ---",
        f"{world.valley.name}: meters={world.valley.meters}",
        f"{world.hero.name}: role={world.hero.role} meters={world.hero.meters} memes={world.hero.memes}",
        f"{world.elder.name}: role={world.elder.role} meters={world.elder.meters} memes={world.elder.memes}",
        f"gift: name={world.gift.name!r} material={world.gift.material!r} shared={world.gift.shared} useful={world.gift.useful}",
        f"solved={world.solved} moral={world.facts.get('moral', '')!r}",
    ])


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(CASES_LIST) if args.all else args.n
    samples: list[StorySample] = []
    for i in range(count):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
