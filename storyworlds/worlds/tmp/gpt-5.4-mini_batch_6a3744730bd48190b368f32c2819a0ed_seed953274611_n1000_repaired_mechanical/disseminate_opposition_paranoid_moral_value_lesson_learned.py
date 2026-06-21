#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/disseminate_opposition_paranoid_moral_value_lesson_learned.py
==============================================================================================

A standalone storyworld for a tiny pirate tale about a rumor, a nervous worry,
and the crew learning that teamwork and calm honesty beat fear.

The seed words are woven into the simulated world:
- disseminate
- opposition
- paranoid

Features:
- Moral Value
- Lesson Learned
- Teamwork

The style leans pirate-tale: a small crew, a worrying message, a turn toward
cooperation, and a final image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class CrewSetting:
    id: str
    scene: str
    place_line: str
    goal: str
    finale: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rumor:
    id: str
    message: str
    source: str
    target: str
    spread_verb: str
    opposition: str
    calm_phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    rumor: str
    response: str
    captain: str
    sailor: str
    captain_gender: str
    sailor_gender: str
    parent: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "deck": CrewSetting(
        id="deck",
        scene="a windy ship deck",
        place_line="The ship deck shone with salt spray, ropes, and a bright lantern at the mast.",
        goal="find the missing map",
        finale="sailed on together under a kinder sky",
    ),
    "harbor": CrewSetting(
        id="harbor",
        scene="a busy harbor",
        place_line="The harbor was full of gull cries, creaking docks, and bobbing boats.",
        goal="prepare the boat for the tide",
        finale="worked on the boat side by side as the tide rolled in",
    ),
    "island": CrewSetting(
        id="island",
        scene="a little island camp",
        place_line="The island camp was ringed by palm trees, driftwood, and a safe fire pit.",
        goal="search for the buried chest",
        finale="finished the day with a shared laugh by the water",
    ),
}

RUMORS = {
    "storm": Rumor(
        id="storm",
        message="a storm is coming",
        source="a whisper from the lookout",
        target="the dark clouds",
        spread_verb="disseminate",
        opposition="opposition",
        calm_phrase="check the sky and the map before jumping to fear",
        tags={"disseminate", "paranoid", "teamwork", "moral"},
    ),
    "ghost": Rumor(
        id="ghost",
        message="a ghost is aboard",
        source="a shaky tale from the cargo hold",
        target="the empty shadows",
        spread_verb="disseminate",
        opposition="opposition",
        calm_phrase="look for footprints, loose boards, and real signs first",
        tags={"disseminate", "paranoid", "teamwork", "moral"},
    ),
    "share": Rumor(
        id="share",
        message="the captain hides the treasure",
        source="a grumbly misunderstanding",
        target="the captain's locked chest",
        spread_verb="disseminate",
        opposition="opposition",
        calm_phrase="ask together and listen before trusting a rumor",
        tags={"disseminate", "paranoid", "teamwork", "moral"},
    ),
}

RESPONSES = {
    "listen": Response(
        id="listen",
        sense=3,
        power=3,
        text="listened, checked the clue together, and found there was no need for panic",
        fail="tried to calm everyone, but the worry had already spread too far",
        qa_text="calmed the crew by checking the clue together",
        tags={"teamwork", "moral"},
    ),
    "signal": Response(
        id="signal",
        sense=3,
        power=4,
        text="raised a lantern signal, gathered the crew, and turned the worry into a plan",
        fail="raised the signal too late, after the crew had already gone fearful",
        qa_text="gathered the crew with a lantern signal and made a plan",
        tags={"teamwork", "moral"},
    ),
    "divide": Response(
        id="divide",
        sense=1,
        power=1,
        text="sent everyone off alone, which only made the fear wander farther",
        fail="split the crew apart, but that only made the fear stronger",
        qa_text="sent the crew apart and failed to stop the fear",
        tags={"opposition", "paranoid"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Eli"]
PARENT_NAMES = ["mother", "father"]
SETTINGS_ORDER = list(SETTINGS)
RUMOR_ORDER = list(RUMORS)
RESPONSE_ORDER = list(RESPONSES)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for rid, rumor in RUMORS.items():
            for resp in RESPONSES.values():
                if resp.sense >= 2 and "teamwork" in rumor.tags:
                    combos.append((sid, rid, resp.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate tale storyworld: rumor, opposition, paranoia, and teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rumor", choices=RUMORS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("--name")
    ap.add_argument("--sailor")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sailor-gender", dest="sailor_gender", choices=["girl", "boy"])
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


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("That response is too weak and only makes the fear spread.")

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.rumor is None or c[1] == args.rumor)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, rumor, response = rng.choice(sorted(combos))
    captain_gender = args.gender or rng.choice(["girl", "boy"])
    sailor_gender = args.sailor_gender or ("boy" if captain_gender == "girl" else "girl")
    captain = args.name or choose_name(rng, captain_gender)
    sailor = args.sailor or choose_name(rng, sailor_gender)
    if sailor == captain:
        sailor = choose_name(rng, sailor_gender)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(
        setting=setting,
        rumor=rumor,
        response=response,
        captain=captain,
        sailor=sailor,
        captain_gender=captain_gender,
        sailor_gender=sailor_gender,
        parent=parent,
    )


def _spread_rumor(world: World, rumor: Rumor) -> None:
    crew = world.entities["crew"]
    crew.meters["buzz"] += 1
    crew.memes["paranoid"] += 1
    crew.memes["opposition"] += 1
    world.say(
        f"{rumor.message.capitalize()} -- so the whisper {rumor.spread_verb} across the deck, "
        f"and the crew's minds began to race."
    )


def _resolve(world: World, response: Response, rumor: Rumor) -> None:
    crew = world.entities["crew"]
    captain = world.entities["captain"]
    sailor = world.entities["sailor"]
    if response.sense >= 2:
        crew.memes["teamwork"] += 1
        captain.memes["calm"] += 1
        sailor.memes["trust"] += 1
        world.say(
            f"{captain.id} and {sailor.id} {response.text}."
        )
        world.say(
            f"That was the moral value of the day: when a crew feels paranoid, it can still "
            f"choose teamwork instead of opposition."
        )
    else:
        crew.memes["fear"] += 1
        world.say(
            f"{captain.id} and {sailor.id} {response.fail}."
        )


def tell(setting: CrewSetting, rumor: Rumor, response: Response,
         captain: str, sailor: str, captain_gender: str, sailor_gender: str,
         parent: str) -> World:
    world = World()
    cap = world.add(Entity(id=captain, kind="character", type=captain_gender, role="captain"))
    sail = world.add(Entity(id=sailor, kind="character", type=sailor_gender, role="sailor"))
    crew = world.add(Entity(id="crew", kind="character", type="crew", label="the crew"))

    cap.memes["doubt"] = 1.0
    sail.memes["worry"] = 1.0
    crew.meters["buzz"] = 0.0

    world.say(
        f"On {setting.scene}, {cap.id} and {sail.id} were part of the same small crew. {setting.place_line}"
    )
    world.say(
        f"{cap.id} liked to keep watch, while {sail.id} listened closely to every tale."
    )
    world.para()
    world.say(
        f"Then a rumor tried to {rumor.spread_verb} itself: {rumor.message}. It came from "
        f"{rumor.source}, and soon every voice sounded a little nervous."
    )
    world.say(
        f"{sail.id} looked toward {rumor.target} and got a little paranoid."
    )
    world.say(
        f'"Maybe we should not believe that yet," {cap.id} said, because {rumor.calm_phrase}.'
    )
    world.para()
    _spread_rumor(world, rumor)
    _resolve(world, response, rumor)
    world.para()
    if response.sense >= 2:
        world.say(
            f"Together they checked the ropes, the sky, and the lanterns. No danger was hiding there."
        )
        world.say(
            f"In the end, the crew learned that a good moral value is to ask, listen, and work together."
        )
        world.say(
            f"By evening, {setting.finale}."
        )
    else:
        world.say(
            f"The crew had to stop and start again, this time with honest questions and a shared plan."
        )
    world.facts.update(
        setting=setting,
        rumor=rumor,
        response=response,
        captain=cap,
        sailor=sail,
        crew=crew,
        outcome="teamwork" if response.sense >= 2 else "paranoid",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    rumor = f["rumor"]
    return [
        f"Write a pirate tale for a young child that includes the words {rumor.spread_verb}, {rumor.opposition}, and paranoid.",
        f"Tell a story where two pirates worry about {rumor.message} but choose teamwork and a moral value instead of fear.",
        f"Write a short children's story about a rumor spreading on a ship and a lesson learned about staying calm.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cap = f["captain"]
    sail = f["sailor"]
    rumor: Rumor = f["rumor"]
    response: Response = f["response"]
    setting: CrewSetting = f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {cap.id} and {sail.id}, two pirates on {setting.scene}. They are the ones who have to deal with the rumor."),
        ("What rumor caused trouble?",
         f"The rumor was that {rumor.message}. It made the crew feel paranoid before they stopped and checked what was true."),
        ("How did they fix the problem?",
         f"They used teamwork and {response.qa_text}. That turned the opposition into a calm plan."),
        ("What lesson did they learn?",
         f"They learned that a moral value is to ask questions and stay calm before spreading a rumor. That lesson kept the crew together."),
    ]
    if f["outcome"] == "teamwork":
        qa.append((
            "How did the story end?",
            f"It ended with the crew working together and feeling steady again. The fear did not lead them apart."
        ))
    return qa


KNOWLEDGE = {
    "disseminate": [("What does disseminate mean?",
                    "Disseminate means to spread something out so more people hear it or see it.")],
    "paranoid": [("What does paranoid mean?",
                 "Paranoid means very nervous and afraid, even when you are not sure something bad is really happening.")],
    "teamwork": [("What is teamwork?",
                  "Teamwork is when people help each other and work together toward one goal.")],
    "moral": [("What is a moral value?",
                "A moral value is a lesson about how to behave kindly and wisely.")],
    "opposition": [("What is opposition?",
                    "Opposition is when people or ideas go against each other.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["rumor"].tags)
    out = []
    for key in ["disseminate", "opposition", "paranoid", "teamwork", "moral"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_response_ids() -> list[str]:
    return [rid for rid, resp in RESPONSES.items() if resp.sense >= 2]


ASP_RULES = r"""
valid(S,R,P) :- setting(S), rumor(R), response(P), sense(P,N), N >= 2.
outcome(teamwork) :- response(P), sense(P,N), N >= 2.
outcome(paranoid) :- response(P), sense(P,N), N < 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, r in RUMORS.items():
        lines.append(asp.fact("rumor", rid))
        for t in sorted(r.tags):
            lines.append(asp.fact("tag", rid, t))
    for pid, p in RESPONSES.items():
        lines.append(asp.fact("response", pid))
        lines.append(asp.fact("sense", pid, p.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generate() completed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection(response: Response) -> str:
    return f"(Refusing response '{response.id}': it is too weak and only feeds the fear.)"


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.rumor not in RUMORS:
        raise StoryError("Unknown rumor.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    world = tell(
        SETTINGS[params.setting],
        RUMORS[params.rumor],
        RESPONSES[params.response],
        params.captain,
        params.sailor,
        params.captain_gender,
        params.sailor_gender,
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_rejection(RESPONSES[args.response]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.rumor is None or c[1] == args.rumor)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, rumor, response = rng.choice(sorted(combos))
    captain_gender = args.gender or rng.choice(["girl", "boy"])
    sailor_gender = args.sailor_gender or ("boy" if captain_gender == "girl" else "girl")
    captain = args.name or choose_name(rng, captain_gender)
    sailor = args.sailor or choose_name(rng, sailor_gender)
    if sailor == captain:
        sailor = choose_name(rng, sailor_gender)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(
        setting=setting,
        rumor=rumor,
        response=response,
        captain=captain,
        sailor=sailor,
        captain_gender=captain_gender,
        sailor_gender=sailor_gender,
        parent=parent,
    )


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_sample_args(seed: int = 777) -> StoryParams:
    return resolve_params(build_parser().parse_args([]), random.Random(seed))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, rumor, response) combos:\n")
        for s, r, p in combos:
            print(f"  {s:8} {r:8} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(setting="deck", rumor="storm", response="listen",
                        captain="Lily", sailor="Tom", captain_gender="girl",
                        sailor_gender="boy", parent="mother"),
            StoryParams(setting="harbor", rumor="ghost", response="signal",
                        captain="Mia", sailor="Ben", captain_gender="girl",
                        sailor_gender="boy", parent="father"),
            StoryParams(setting="island", rumor="share", response="listen",
                        captain="Ava", sailor="Leo", captain_gender="girl",
                        sailor_gender="boy", parent="mother"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
