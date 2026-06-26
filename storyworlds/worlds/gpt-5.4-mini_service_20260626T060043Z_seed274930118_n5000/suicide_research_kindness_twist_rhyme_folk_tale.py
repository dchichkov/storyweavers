#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/suicide_research_kindness_twist_rhyme_folk_tale.py
===============================================================================================================

A small folk-tale storyworld about a village scholar who researches a hard,
sad word, then finds a kinder twist.

The seed image is a quiet old tale:
- A little village has a worn book of sayings.
- A young researcher keeps hearing the word "suicide" in an old cautionary rhyme.
- The villagers grow afraid and start repeating the word without understanding it.
- A kind elder turns the story: instead of fear, the village makes a plan for
  care, listening, and asking for help when someone seems deeply sad.

This world stays child-facing and non-graphic. The hard word is handled with
care, and the turn is about kindness, support, and speaking up early.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    label: str = ""
    phrase: str = ""
    type: str = "thing"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "elder_woman"}
        male = {"boy", "man", "father", "elder_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    weather: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Topic:
    id: str
    keyword: str
    research_question: str
    tension: str
    folk_rhyme: str
    twist: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "village": Setting(place="the little village", weather="misty", affordances={"research", "rhyme"}),
    "library": Setting(place="the old village library", weather="quiet", affordances={"research", "rhyme"}),
    "hearth": Setting(place="the hearth room", weather="warm", affordances={"rhyme"}),
}

TOPICS = {
    "suicide": Topic(
        id="suicide",
        keyword="suicide",
        research_question="why the sad old rhyme was scaring the village",
        tension="the villagers kept whispering the hard word and grew afraid",
        folk_rhyme="When a rhyme is dark and cold, listen close and do not scold.",
        twist="the elder showed that the village needed care, listening, and help, not fear",
        lesson="when someone is deeply sad, kindness and speaking up matter",
        tags={"sad", "help", "kindness", "research", "rhyme"},
    ),
    "lost_song": Topic(
        id="lost_song",
        keyword="lost song",
        research_question="who had hidden the missing line of the old song",
        tension="everyone could sing the tune, but nobody could remember the last line",
        folk_rhyme="A song half-known will wander far, like moonlight caught in a jar.",
        twist="the missing line was tucked into the baker's recipe book all along",
        lesson="careful looking and patient listening can solve a mystery",
        tags={"research", "rhyme", "kindness"},
    ),
    "river_secret": Topic(
        id="river_secret",
        keyword="river secret",
        research_question="why the river stones kept shining after rain",
        tension="the children wanted an answer, but the grown-ups only shrugged",
        folk_rhyme="If the river keeps a gleam, follow patient steps and dream.",
        twist="the shine came from tiny mica flakes in the bank",
        lesson="small clues can explain a big wonder",
        tags={"research", "rhyme"},
    ),
}

RESEARCHERS = {
    "mira": {"type": "girl", "traits": ["curious", "gentle", "brave"]},
    "oren": {"type": "boy", "traits": ["careful", "kind", "patient"]},
    "sela": {"type": "woman", "traits": ["wise", "steady", "kind"]},
    "tobin": {"type": "man", "traits": ["soft-spoken", "patient", "helpful"]},
}

Elders = {
    "grandmother": {"type": "elder_woman", "label": "Grandmother Iva"},
    "grandfather": {"type": "elder_man", "label": "Grandfather Bram"},
}

# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    topic: str
    researcher: str
    elder: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when it has a place, a researcher, and one topic.
valid_story(P, T, R, E) :- setting(P), topic(T), researcher(R), elder(E).

% The suicide topic is only allowed in this world when the twist is care and support.
safe_topic(suicide) :- topic(suicide).

% A research story is valid if the setting allows research and the topic exists.
valid_research_story(P, T) :- setting(P), topic(T), affords(P, research).

#show valid_story/4.
#show valid_research_story/2.
#show safe_topic/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", pid, a))
    for tid in TOPICS:
        lines.append(asp.fact("topic", tid))
    for rid in RESEARCHERS:
        lines.append(asp.fact("researcher", rid))
    for eid in Elders:
        lines.append(asp.fact("elder", eid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_models() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4.\n#show valid_research_story/2.\n#show safe_topic/1."))
    return [tuple(str(a) for a in atom.arguments) for atom in model]


def asp_verify() -> int:
    py = set(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    cl = set(asp.atoms(model, "valid_story"))
    if cl == py:
        print(f"OK: ASP and Python agree on {len(py)} valid story combos.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "research" not in setting.affordances:
            continue
        for topic in TOPICS:
            for researcher in RESEARCHERS:
                for elder in Elders:
                    combos.append((place, topic, researcher, elder))
    return combos


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    topic = TOPICS[params.topic]
    researcher_cfg = RESEARCHERS[params.researcher]
    elder_cfg = Elders[params.elder]

    if "research" not in setting.affordances and topic.id == "suicide":
        raise StoryError("This place is not a good place for careful research on a hard topic.")

    world = World(setting=setting)
    researcher = world.add(Entity(
        id=params.researcher,
        kind="character",
        type=researcher_cfg["type"],
        traits=list(researcher_cfg["traits"]),
        meters={"attention": 1.0, "courage": 1.0},
        memes={"curiosity": 1.0, "kindness": 1.0},
    ))
    elder = world.add(Entity(
        id=params.elder,
        kind="character",
        type=elder_cfg["type"],
        label=elder_cfg["label"],
        traits=["wise", "kind"],
        meters={"listening": 1.0},
        memes={"care": 1.0},
    ))
    book = world.add(Entity(
        id="book",
        kind="thing",
        type="book",
        label="old book",
        phrase="the old book of village sayings",
        owner=params.researcher,
        caretaker=params.researcher,
        meters={"pages": 1.0},
    ))
    world.facts.update(
        setting=setting,
        topic=topic,
        researcher=researcher,
        elder=elder,
        book=book,
        researched=True,
        twist=False,
        resolved=False,
    )
    return world


def tell(world: World) -> None:
    f = world.facts
    setting: Setting = f["setting"]
    topic: Topic = f["topic"]
    researcher: Entity = f["researcher"]
    elder: Entity = f["elder"]

    world.say(
        f"In {setting.place}, {researcher.id} was a {researcher.traits[0]} little researcher "
        f"who loved asking about old words and older songs."
    )
    world.say(
        f"One misty morning, {researcher.id} set out to research {topic.keyword} "
        f"because {topic.research_question}."
    )
    world.say(
        f"The village had started to whisper the hard word, and that made the air feel heavy; "
        f"{topic.tension}."
    )

    world.para()
    world.say(f'Near the library shelf, {researcher.id} found a rhyme written in a narrow hand:')
    world.say(f'"{topic.folk_rhyme}"')
    world.say(
        f"{researcher.id} did not laugh at the rhyme. {researcher.pronoun().capitalize()} copied it down "
        f"carefully and brought it to {elder.label}."
    )
    world.say(
        f'{elder.label} looked at the page, nodded slowly, and said, '
        f'"This is a story about fear, but we can make it a story about help."'
    )

    world.para()
    world.say(
        f"Then came the twist: {topic.twist}. "
        f"{elder.label} told the villagers to stop repeating the word as if it were a game and "
        f"start checking on anyone who seemed very sad, alone, or quiet for too long."
    )
    world.say(
        f"{researcher.id} wrote the new lesson in the book: {topic.lesson}."
    )
    world.say(
        f"By sunset, the library lamp glowed, the rhyme sounded gentler, and the village had a plan "
        f"to listen, sit together, and ask for help."
    )

    f["twist"] = True
    f["resolved"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    topic: Topic = f["topic"]
    researcher: Entity = f["researcher"]
    elder: Entity = f["elder"]
    return [
        f'Write a short folk tale about a researcher named {researcher.id} who investigates "{topic.keyword}" and finds a kinder answer.',
        f"Tell a gentle story in a village where {elder.label} helps {researcher.id} understand a scary old rhyme.",
        f'Write a child-friendly tale that includes research, a twist, and a rhyme about "{topic.keyword}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    topic: Topic = f["topic"]
    researcher: Entity = f["researcher"]
    elder: Entity = f["elder"]
    qa = [
        QAItem(
            question=f"What did {researcher.id} research in the village?",
            answer=f"{researcher.id} researched {topic.keyword} because {topic.research_question}.",
        ),
        QAItem(
            question=f"Who helped {researcher.id} understand the old rhyme?",
            answer=f"{elder.label} helped {researcher.id} understand it and gave the story a kinder meaning.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="The village stopped treating the hard word like a rumor and started treating it like a call for kindness, listening, and help.",
        ),
    ]
    if f.get("twist"):
        qa.append(
            QAItem(
                question="What was the twist in the story?",
                answer=topic.twist.capitalize() + ".",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    topic: Topic = f["topic"]
    out = [
        QAItem(
            question="What is research?",
            answer="Research is careful looking, asking, and reading to learn what is true.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little bit of language where sounds at the ends match or nearly match, like in a song or poem.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, comfort, and care about someone else.",
        ),
    ]
    if topic.id == "suicide":
        out.append(
            QAItem(
                question="Why should people treat the word suicide with care?",
                answer="Because it refers to a very serious danger and a person may need immediate help, support, and a trusted adult right away.",
            )
        )
    return out


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
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  facts={ {k: type(v).__name__ for k, v in world.facts.items()} }")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="village", topic="suicide", researcher="mira", elder="grandmother"),
    StoryParams(place="library", topic="lost_song", researcher="oren", elder="grandfather"),
    StoryParams(place="village", topic="river_secret", researcher="sela", elder="grandmother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about research, kindness, rhyme, and a twist."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--topic", choices=TOPICS)
    ap.add_argument("--researcher", choices=RESEARCHERS)
    ap.add_argument("--elder", choices=Elders)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    filtered = []
    for place, topic, researcher, elder in combos:
        if args.place is not None and place != args.place:
            continue
        if args.topic is not None and topic != args.topic:
            continue
        if args.researcher is not None and researcher != args.researcher:
            continue
        if args.elder is not None and elder != args.elder:
            continue
        filtered.append((place, topic, researcher, elder))
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, topic, researcher, elder = rng.choice(filtered)
    return StoryParams(place=place, topic=topic, researcher=researcher, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4.\n#show valid_research_story/2.\n#show safe_topic/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4.\n#show valid_research_story/2.\n#show safe_topic/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4.\n#show valid_research_story/2.\n#show safe_topic/1."))
        print(f"{len(asp.atoms(model, 'valid_story'))} valid_story atoms")
        for atom in asp.atoms(model, "valid_story"):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.researcher} / {p.topic} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
