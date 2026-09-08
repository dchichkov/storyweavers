#!/usr/bin/env python3
"""
A standalone Storyweavers world: a heartwarming parade surprise.

Premise:
- A small parade is being prepared in a town square.
- A sailor and an infantry drummer join the crowd for the march.
- A simple twist changes the plan when a shared duty is overlooked.
- Kindness, quick thinking, and teamwork turn the twist into a happy ending.

This script follows the Storyworld contract:
- standalone stdlib Python
- lazy ASP import for verification/query modes
- world simulation with physical meters and emotional memes
- StorySample/QAItem/StoryError from storyworlds.results
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    location: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ["distance", "wetness", "rust", "dust", "lost", "tilt", "weight"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "joy", "trust", "pride", "relief", "courage", "care"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    name: str = "Mira"
    sailor: str = "Jonah"
    infantry: str = "Bram"
    twist: int = 0
    voice: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class TwistCase:
    plan: str
    setting: str
    duty: str
    twist_event: str
    clue: str
    false_guess: str
    dialogue: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending: str


TWIST_CASES = [
    TwistCase(
        plan="a ribbon parade with paper waves and tinny drums",
        setting="the town square beside the fountain",
        duty="carry the lantern rope and ring the bell at each corner",
        twist_event="the parade banner slipped from the mayor's cart just before the first drumbeat",
        clue="a wet ribbon trail led from the fountain to the music stand",
        false_guess="someone thought a gust had carried the banner away",
        dialogue="Mira said, 'Let's follow the ribbon.' Jonah replied, 'And Bram can watch the cart wheels.'",
        discovery="they found the banner folded neatly behind the drummer's stool",
        cause="Jonah had reached for a loose knot, knocked the banner down, and tucked it aside so nobody would trip",
        repair="they re-tied the rope, lifted the banner back onto its poles, and marched together in step",
        proof="the banner stayed high, the lantern rope hung straight, and no one stumbled",
        lesson="A small mistake becomes easier to fix when people speak kindly and work side by side.",
        ending="By the time the last drum faded, the banner was flying again above smiling faces.",
    ),
    TwistCase(
        plan="a seaside parade with shells on strings and bright blue scarves",
        setting="the boardwalk near the harbor",
        duty="guide the children past the sea wall and keep the parade line steady",
        twist_event="the sailor's whistle went missing just as the parade line began to wobble",
        clue="the whistle cord was tangled around a crate of apples",
        false_guess="the infantry drummer thought the whistle might have fallen into the water",
        dialogue="Jonah said, 'I lost track of it when I helped with the apples.' Bram answered, 'Then let's look where your hands last worked.'",
        discovery="they found the whistle in Jonah's coat pocket, safe beside a folded map",
        cause="Jonah had slipped it into the pocket while carrying snacks and forgotten it there",
        repair="they laughed, gave the whistle back its cord, and used the map to guide the parade",
        proof="the whistle sang clearly and the children marched without drifting from the line",
        lesson="A helpful twist can still end well when everyone keeps calm and checks the facts.",
        ending="Salt wind blew over the boardwalk, and the rescued whistle led the parade home in a merry tune.",
    ),
    TwistCase(
        plan="a harvest parade with leaf crowns and a drumline of wooden boxes",
        setting="the market lane under orange bunting",
        duty="carry the basket of apples for the closing feast",
        twist_event="the feast basket tipped and rolled beneath the pie table",
        clue="one apple left a red track on the tablecloth",
        false_guess="the crowd thought the basket had gone missing in the noise",
        dialogue="Bram said, 'That red line points under the table.' Mira smiled and said, 'Then the basket did not vanish at all.'",
        discovery="they slid the basket out from under the pie table and found every apple still inside",
        cause="Bram had set the basket down too fast while helping a child with a scarf",
        repair="they cleaned the cloth, shared the apples, and placed the basket where two hands could reach it",
        proof="the basket sat steady, the cloth was clean, and the feast began on time",
        lesson="Looking closely can turn worry into relief.",
        ending="The parade ended with apple slices for everyone and warm laughter in the market lane.",
    ),
    TwistCase(
        plan="a lantern parade through the little park",
        setting="the path by the pond and the willow tree",
        duty="hold the lantern pole until the music started",
        twist_event="the lantern glow faded because the candle inside had blown out",
        clue="a puff of smoke curled toward the willow leaves",
        false_guess="someone believed the lantern had broken for good",
        dialogue="Mira whispered, 'It only needs a new flame.' Jonah said, 'Then let's borrow the shelter of the willow.'",
        discovery="they relit the candle under a coat, and the lantern blinked awake",
        cause="Jonah had walked too fast in the breeze and forgotten the lantern cap",
        repair="they covered the flame, fixed the cap, and walked slower together",
        proof="the lantern stayed bright all the way past the pond",
        lesson="When a light goes out, patience and help can bring it back.",
        ending="Under the willow, the lantern glowed softly like a tiny moon in caring hands.",
    ),
    TwistCase(
        plan="a spring parade with flower ribbons and hand-painted signs",
        setting="the school steps at the center of town",
        duty="unfurl the big welcome sign at the start",
        twist_event="the sign flipped backward and showed only the blank cloth side",
        clue="paint flecks marked the inside hem",
        false_guess="the infantry drummer worried the sign had been ruined",
        dialogue="Mira said, 'It is only turned around.' Bram laughed, 'Then the heart of the parade is still there, just waiting.'",
        discovery="they turned the sign right-side-up and saw the words shining cleanly in blue paint",
        cause="Mira had rolled the sign too tightly and twisted the poles by mistake",
        repair="they loosened the poles, smoothed the cloth, and carried the sign together",
        proof="the welcome words faced the crowd and stayed flat in the breeze",
        lesson="A twist can hide something good without taking it away.",
        ending="The crowd cheered when the welcome sign opened like a bright spring smile.",
    ),
    TwistCase(
        plan="a ribbon parade for the new library",
        setting="the stone path outside the library door",
        duty="ring the small bell each time the parade passed the steps",
        twist_event="the bell's clapper jammed with a scrap of paper",
        clue="the scrap matched the library's book tags",
        false_guess="someone thought the bell was broken beyond repair",
        dialogue="Jonah said, 'Wait. The paper is stuck, not the bell itself.' Bram answered, 'Then the bell can ring again.'",
        discovery="they pulled out the scrap and heard the bell sing at once",
        cause="Bram had tucked a tag into the bell to keep his hands free, then forgotten it",
        repair="they taped the tags onto a tray, polished the bell, and resumed the parade",
        proof="the bell rang clear at every step and the books stayed neat on their shelves",
        lesson="A small obstacle is easier to fix than a big fear about it.",
        ending="The library door opened to a bell that rang like a happy promise.",
    ),
    TwistCase(
        plan="a coastal parade with flags shaped like waves",
        setting="the harbor stairs at low tide",
        duty="carry a bucket of paint for the final sign",
        twist_event="the paint bucket tilted and left a blue streak across the steps",
        clue="the streak led straight to the sign board",
        false_guess="the sailor blamed the tide for the mess",
        dialogue="Bram said, 'The bucket tipped because the lid was loose.' Jonah replied, 'Then the tide is not to blame.'",
        discovery="they found the missing lid under the sign board and cleaned the steps",
        cause="Jonah had rushed to wave at a ferry and bumped the bucket with his boot",
        repair="they scrubbed the steps, tightened the lid, and painted the sign together",
        proof="the steps were dry and the sign dried without another drip",
        lesson="Being honest about an accident helps everyone move forward.",
        ending="Blue flags fluttered over clean harbor steps as the parade walked on with pride.",
    ),
    TwistCase(
        plan="a neighborhood parade with kites and a brass whistle",
        setting="the grassy hill behind the bakery",
        duty="lift the kites when the march began",
        twist_event="the kites tangled in one long knot right at the hilltop",
        clue="the knot was tied around the whistle cord",
        false_guess="the infantry drummer thought the wind had ruined the day",
        dialogue="Mira said, 'The wind made a knot, not a disaster.' Bram grinned, 'Then we untie one loop at a time.'",
        discovery="they loosened the cord and sent the kites up one by one",
        cause="Bram had wrapped the cord around his wrist while carrying buns and slipped in the grass",
        repair="they untangled the line, shared the buns, and launched the kites in a neat row",
        proof="the kites climbed cleanly and the whistle cord stayed free",
        lesson="Careful hands can fix what a clumsy moment tied together.",
        ending="Above the bakery hill, the kites rose like bright birds over a happy parade.",
    ),
]


@dataclass
class World:
    hero: Entity
    sailor: Entity
    infantry: Entity
    banner: Entity
    bell: Entity
    lantern: Entity
    square: Entity
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


def _new_entity(eid: str, kind: str, type_: str, label: str, phrase: str = "", **kwargs) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, phrase=phrase, **kwargs)


def build_world(params: StoryParams) -> World:
    hero = _new_entity(params.name, "character", "girl", "the child", meters={}, memes={})
    sailor = _new_entity(params.sailor, "character", "man", "the sailor", meters={}, memes={})
    infantry = _new_entity(params.infantry, "character", "man", "the infantry drummer", meters={}, memes={})
    banner = _new_entity("banner", "thing", "cloth", "banner", "the parade banner")
    bell = _new_entity("bell", "thing", "bell", "small bell", "a little parade bell")
    lantern = _new_entity("lantern", "thing", "lantern", "lantern", "a paper lantern")
    square = _new_entity("square", "place", "place", "town square", "the town square")
    return World(hero=hero, sailor=sailor, infantry=infantry, banner=banner, bell=bell, lantern=lantern, square=square)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, s, i = world.hero, world.sailor, world.infantry
    b, bell, lan = world.banner, world.bell, world.lantern
    case = TWIST_CASES[params.twist % len(TWIST_CASES)]
    h.memes["worry"] += 1
    s.memes["pride"] += 1
    i.memes["care"] += 1
    b.meters["lost"] = 1
    world.say(f"In {case.setting}, the town was getting ready for {case.plan}.")
    world.say(f"{h.id}, {s.id}, and {i.id} helped with the parade, and each had a job: {case.duty}.")
    world.say(f"Then the twist arrived: {case.twist_event}.")
    world.para()
    world.say(f"That left everyone still for a moment. {case.false_guess.capitalize()}, but {h.id} looked closer at the clues.")
    world.say(f"Near the parade path was a clue: {case.clue}.")
    world.say(f"{h.id} thought hard, and the quiet thought became a plan: follow the clue before guessing.")
    world.say(case.dialogue)
    world.say(f"Together, they searched until {case.discovery}.")
    b.meters["lost"] = 0
    b.carried_by = h.id
    world.para()
    world.say(f"When they understood the cause, they learned that {case.cause}.")
    world.say(f"Instead of scolding, the three of them smiled, fixed the problem, and {case.repair}.")
    h.memes["joy"] += 2
    s.memes["relief"] += 2
    i.memes["relief"] += 2
    h.memes["trust"] += 1
    s.memes["trust"] += 1
    i.memes["trust"] += 1
    world.say(f"They checked their work: {case.proof}.")
    world.say(f"In the end, {case.lesson}")
    world.para()
    world.say(f"{case.ending}")
    world.facts.update(
        hero=h,
        sailor=s,
        infantry=i,
        banner=b,
        bell=bell,
        lantern=lan,
        square=world.square,
        plan=case.plan,
        setting=case.setting,
        duty=case.duty,
        twist_event=case.twist_event,
        clue=case.clue,
        false_guess=case.false_guess,
        discovery=case.discovery,
        cause=case.cause,
        repair=case.repair,
        proof=case.proof,
        lesson=case.lesson,
        ending=case.ending,
        voice=params.voice,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    h, s, i = world.facts["hero"], world.facts["sailor"], world.facts["infantry"]
    q1 = [
        f"What happened to interrupt {world.facts['plan']}?",
        f"Why did the parade almost stop?",
        f"What was the twist in the story?",
        f"What problem changed the parade plan?",
    ][world.facts["voice"] % 4]
    q2 = [
        f"Which clue helped {h.id} solve the problem?",
        f"What did {h.id} notice before guessing?",
        f"How did the team know where to search?",
        f"What evidence pointed them to the answer?",
    ][world.facts["voice"] % 4]
    q3 = [
        f"What did {s.id} and {i.id} do to help repair the problem?",
        f"How did the sailor and infantry drummer work with {h.id}?",
        f"What did the team do after finding the cause?",
        f"How was the parade fixed in a kind way?",
    ][world.facts["voice"] % 4]
    q4 = [
        "What did the story show about a small mistake?",
        "What lesson did the parade team learn?",
        "How did the characters turn worry into relief?",
        "What made the ending heartwarming?",
    ][world.facts["voice"] % 4]
    return [
        QAItem(
            question=q1,
            answer=f"The parade was interrupted when {world.facts['twist_event']}. That changed what the helpers needed to do.",
        ),
        QAItem(
            question=q2,
            answer=f"{h.id} noticed {world.facts['clue']} and trusted that more than the first guess. The clue led them to {world.facts['discovery']}.",
        ),
        QAItem(
            question=q3,
            answer=f"{s.id}, {i.id}, and {h.id} worked together to {world.facts['repair']}. Their teamwork fixed the parade safely.",
        ),
        QAItem(
            question=q4,
            answer=f"They learned that {world.facts['lesson']} The story ends with {world.facts['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a cheerful procession where people march, ride, or walk together in a special line for others to see.",
        ),
        QAItem(
            question="What is a sailor?",
            answer="A sailor is a person who works on boats or ships and knows how to handle the water and wind.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry is the part of an army that travels and fights on foot instead of in vehicles.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that makes the plan go in a new direction.",
        ),
        QAItem(
            question="What does heartwarming mean?",
            answer="Heartwarming means it makes people feel cared for, hopeful, and glad inside.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly heartwarming story about a parade in {world.facts['setting']} where a sailor and infantry helper face a twist.",
        f"Tell a short scene in which {world.facts['hero'].id} uses a clue and a kind conversation to solve {world.facts['twist_event']}.",
        "Create an ending where the parade is repaired through teamwork, with one brief back-and-forth spoken exchange that changes what someone does.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in [world.hero, world.sailor, world.infantry, world.banner, world.bell, world.lantern, world.square]:
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(parade_story).
requires(parade_story, parade).
requires(parade_story, sailor).
requires(parade_story, infantry).
requires(parade_story, twist).
heartwarming(parade_story).

valid_story(S) :- setting(S), requires(S, parade), requires(S, sailor), requires(S, infantry), requires(S, twist), heartwarming(S).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    return "\n".join(
        [
            asp.fact("setting", "parade_story"),
            asp.fact("requires", "parade_story", "parade"),
            asp.fact("requires", "parade_story", "sailor"),
            asp.fact("requires", "parade_story", "infantry"),
            asp.fact("requires", "parade_story", "twist"),
            asp.fact("heartwarming", "parade_story"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import
    models = asp.one_model(asp_program("#show valid_story/1."))
    ok = any(atom.name == "valid_story" for atom in models)
    if ok:
        print("OK: ASP rules recognize the parade story domain.")
        return 0
    print("MISMATCH: ASP rules failed to recognize the story domain.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming parade story world.")
    ap.add_argument("--name", default=None)
    ap.add_argument("--sailor", default=None)
    ap.add_argument("--infantry", default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random, sample_seed: int, base_seed: int) -> StoryParams:
    name = args.name or rng.choice(["Mira", "Nina", "Lola", "Tess", "June"])
    sailor = args.sailor or rng.choice(["Jonah", "Marin", "Silas", "Oren", "Theo"])
    infantry = args.infantry or rng.choice(["Bram", "Eli", "Noah", "Perry", "Wren"])
    if len({name, sailor, infantry}) < 3:
        raise StoryError("The three characters must be different.")
    offset = sample_seed - base_seed
    return StoryParams(
        name=name,
        sailor=sailor,
        infantry=infantry,
        twist=offset % len(TWIST_CASES),
        voice=(offset // len(TWIST_CASES)) % 4,
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story="\n\n".join(p for p in world.render().split("\n\n") if p),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(name="Mira", sailor="Jonah", infantry="Bram"),
    StoryParams(name="Nina", sailor="Marin", infantry="Eli"),
    StoryParams(name="Tess", sailor="Silas", infantry="Noah"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(a) for a in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            sample_seed = base_seed + i
            params = resolve_params(args, random.Random(sample_seed), sample_seed, base_seed)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
