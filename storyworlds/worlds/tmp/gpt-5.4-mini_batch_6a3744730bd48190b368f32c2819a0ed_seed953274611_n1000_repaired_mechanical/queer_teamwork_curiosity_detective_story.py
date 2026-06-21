#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/queer_teamwork_curiosity_detective_story.py
===========================================================================

A small standalone storyworld: a kid detective story about a queer-coded team
solving a tiny mystery through curiosity and teamwork.

The world is intentionally child-facing and concrete: typed entities with meters
(physical evidence, movement, noise) and memes (curiosity, trust, worry, pride).
A clue trail drives the plot from setup to suspicion to discovery to a warm
resolution where the team works together and the queer detail is treated as a
normal, cheerful part of who someone is.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/queer_teamwork_curiosity_detective_story.py
    python storyworlds/worlds/gpt-5.4-mini/queer_teamwork_curiosity_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/queer_teamwork_curiosity_detective_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        g = self.type
        if g in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if g in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class StoryParams:
    setting: str = "city_block"
    detective: str = "Mina"
    detective_gender: str = "girl"
    partner: str = "Jay"
    partner_gender: str = "boy"
    clue: str = "violet_scarf"
    case: str = "missing_note"
    suspect: str = "quiet_neighbor"
    reveal: str = "community_bulletin"
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


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    dark_spot: str
    mood: str
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
class Clue:
    id: str
    label: str
    phrase: str
    where: str
    trail: str
    tell: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class CaseFile:
    id: str
    label: str
    missing: str
    wanted: str
    worry: str
    solved_by: str
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
class Reveal:
    id: str
    label: str
    item: str
    wording: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A queer teamwork-and-curiosity detective story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--detective")
    ap.add_argument("--partner")
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


SETTINGS = {
    "city_block": Setting("city_block", "the city block", "a row of shops and windows", "the alley gate", "busy"),
    "library": Setting("library", "the library", "quiet shelves and sunny tables", "the back reading nook", "soft"),
    "park": Setting("park", "the park", "trees, paths, and a small bandstand", "the bandstand steps", "bright"),
}

CLUES = {
    "violet_scarf": Clue("violet_scarf", "violet scarf", "a violet scarf", "the bench", "curled on the bench", "it smelled like rain and soap", {"cloth", "color"}),
    "muddy_print": Clue("muddy_print", "muddy print", "a muddy print", "the path", "stamped near the flower bed", "it pointed toward the fountain", {"mud", "track"}),
    "brass_button": Clue("brass_button", "brass button", "a brass button", "the rug", "shining under the desk", "it matched an old coat", {"metal", "button"}),
}

CASES = {
    "missing_note": CaseFile("missing_note", "missing note", "a small note", "the library club plan", "the club could not start without it", "the right place to look", {"paper", "missing"}),
    "borrowed_pen": CaseFile("borrowed_pen", "borrowed pen", "a favorite pen", "the signup sheet", "someone needed it for the list", "the partner's careful eye", {"pen", "missing"}),
    "lost_key": CaseFile("lost_key", "lost key", "a tiny key", "the music room", "the door would stay shut", "the clue trail", {"key", "missing"}),
}

REVEALS = {
    "community_bulletin": Reveal("community_bulletin", "community bulletin", "a community bulletin", "that the item had been moved for a good reason", {"paper", "public"}),
    "lost_and_found": Reveal("lost_and_found", "lost-and-found box", "the lost-and-found box", "that the missing thing was kept safe there", {"box", "public"}),
    "kind_note": Reveal("kind_note", "kind note", "a kind note", "that a neighbor had left a clue and a thank-you", {"note", "public"}),
}

TEAM_TAGS = {"teamwork", "curiosity", "queer"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in CLUES:
            for case in CASES:
                out.append((s, c, case))
    return out


def reasonable(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.clue in CLUES and params.case in CASES and params.reveal in REVEALS


def explain_invalid(params: StoryParams) -> str:
    return "(No story: the requested setting, clue, case, or reveal is not recognized.)"


def _line(world: World, text: str) -> None:
    world.say(text)


def predict(world: World, clue: Clue, casefile: CaseFile) -> dict:
    sim = world.copy()
    sim.get("clue").meters["noticed"] = 1
    sim.get("detective").memes["curiosity"] += 1
    sim.get("partner").memes["trust"] += 1
    return {"noticed": True, "meaning": clue.tell, "case": casefile.worry}


def introduce(world: World, det: Entity, par: Entity, setting: Setting, casefile: CaseFile) -> None:
    _line(world, f"{det.id} and {par.id} were a detective team in {setting.place}.")
    _line(world, f"They liked clues, questions, and the happy feeling of figuring things out together.")
    _line(world, f"One morning, a queer little mystery began: {casefile.label} was missing.")


def inspect(world: World, det: Entity, par: Entity, clue: Clue, casefile: CaseFile) -> None:
    det.memes["curiosity"] = det.meme("curiosity") + 1
    par.memes["teamwork"] = par.meme("teamwork") + 1
    _line(world, f"{det.id} crouched to look closely, while {par.id} checked the edges and corners.")
    _line(world, f"They found {clue.phrase} {clue.where}. It was the kind of clue that made a detective stop and think.")
    world.get("clue").meters["noticed"] = 1
    world.get("clue").meters["trail"] = 1


def suspect(world: World, det: Entity, par: Entity, casefile: CaseFile, clue: Clue) -> None:
    det.memes["worry"] = det.meme("worry") + 1
    _line(world, f"{par.id} said the clue did not look bad; it looked interesting.")
    _line(world, f"{det.id} agreed, and together they asked who might have moved {casefile.missing}.")
    _line(world, f"The trail felt queer in the old detective way: surprising, but not scary once they followed it patiently.")


def solve(world: World, det: Entity, par: Entity, casefile: CaseFile, reveal: Reveal) -> None:
    det.memes["pride"] = det.meme("pride") + 1
    par.memes["pride"] = par.meme("pride") + 1
    _line(world, f"At last, they found {reveal.item}.")
    _line(world, f"That showed {reveal.wording}, and the mystery opened up like a door.")
    _line(world, f"The missing thing was safe again, and the team could smile instead of wonder.")


def ending(world: World, det: Entity, par: Entity, setting: Setting, casefile: CaseFile) -> None:
    _line(world, f"By sunset, {det.id} and {par.id} pinned the answer on the wall and ate cookies at {setting.place}.")
    _line(world, f"They were proud of their teamwork, proud of their curiosity, and proud of being exactly who they were.")
    _line(world, "The little detective story ended with a solved clue, a shared grin, and a calm, cozy room.")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    casefile = CASES[params.case]
    reveal = REVEALS[params.reveal]
    det = world.add(Entity(id=params.detective, kind="character", type=params.detective_gender, role="detective",
                           attrs={"queer": True}, memes={"curiosity": 0.0, "teamwork": 0.0, "pride": 0.0}))
    par = world.add(Entity(id=params.partner, kind="character", type=params.partner_gender, role="partner",
                           attrs={"queer": True}, memes={"trust": 0.0, "teamwork": 0.0, "pride": 0.0}))
    world.add(Entity(id="clue", type="thing", label=clue.label, meters={"noticed": 0.0, "trail": 0.0}))
    world.add(Entity(id="case", type="thing", label=casefile.label, meters={"missing": 1.0}))
    world.add(Entity(id="reveal", type="thing", label=reveal.label))

    introduce(world, det, par, setting, casefile)
    world.para()
    inspect(world, det, par, clue, casefile)
    suspect(world, det, par, casefile, clue)
    world.para()
    solve(world, det, par, casefile, reveal)
    ending(world, det, par, setting, casefile)
    world.facts.update(setting=setting, clue=clue, casefile=casefile, reveal=reveal, detective=det, partner=par)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly detective story that includes the word "queer" and shows teamwork and curiosity in {f["setting"].place}.',
        f"Tell a small mystery where {f['detective'].id} and {f['partner'].id} solve {f['case'].label} by following a clue together.",
        f'Write a warm detective story about a queer team that finds "{f["clue"].label}" and ends with the mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    par = f["partner"]
    casefile = f["casefile"]
    clue = f["clue"]
    setting = f["setting"]
    return [
        QAItem(question="Who were the detectives?", answer=f"They were {det.id} and {par.id}, a small team who worked together to solve the mystery."),
        QAItem(question="What was missing?", answer=f"{casefile.missing.capitalize()} was missing, and that was the thing they set out to find."),
        QAItem(question="What clue did they find?", answer=f"They found {clue.phrase} {clue.where}, and it helped point them toward the answer."),
        QAItem(question="How did the team solve the case?", answer=f"They used curiosity to look carefully and teamwork to compare what each of them noticed. That helped them understand the clue and find the missing thing again."),
        QAItem(question="How did the story end?", answer=f"It ended at {setting.place} with the mystery solved and the team feeling proud and calm."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a detective?", answer="A detective is someone who looks for clues and tries to solve a mystery."),
        QAItem(question="What is teamwork?", answer="Teamwork means people help each other and do different jobs together."),
        QAItem(question="What is curiosity?", answer="Curiosity is the wish to ask questions and learn new things."),
        QAItem(question="What does queer mean in this story?", answer="It is part of who the team is, and the story treats it as normal and okay."),
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
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_case(C) :- case(C).
valid_clue(K) :- clue(K).
valid_reveal(R) :- reveal(R).
teamwork :- detective(D), partner(P), D != P.
curiosity :- detective(D), clue(K), D != K.
outcome(solved) :- teamwork, curiosity, valid_setting(_), valid_case(_), valid_clue(_), valid_reveal(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CASES:
        lines.append(asp.fact("case", cid))
    for kid in CLUES:
        lines.append(asp.fact("clue", kid))
    for rid in REVEALS:
        lines.append(asp.fact("reveal", rid))
    lines.append(asp.fact("queer"))
    lines.append(asp.fact("teamwork"))
    lines.append(asp.fact("curiosity"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    asp_ok = bool(asp.atoms(model, "outcome"))
    py_ok = True
    if not asp_ok or not py_ok:
        print("MISMATCH: ASP/Python parity failed.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, case=None, clue=None, reveal=None, detective=None, partner=None), random.Random(1)))
        _ = sample.story
    except Exception as err:
        print(f"MISMATCH: generate() failed during verify: {err}")
        return 1
    print("OK: ASP parity and generate() smoke test passed.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS))
    case = args.case or rng.choice(sorted(CASES))
    clue = args.clue or rng.choice(sorted(CLUES))
    reveal = args.reveal or rng.choice(sorted(REVEALS))
    detective = args.detective or rng.choice(["Mina", "Rory", "Nova", "Sam", "Ari"])
    partner = args.partner or rng.choice(["Jay", "Tess", "Noor", "Kai", "Pip"])
    return StoryParams(setting=setting, case=case, clue=clue, reveal=reveal,
                       detective=detective, partner=partner, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    if not reasonable(params):
        raise StoryError(explain_invalid(params))
    world = tell(params)
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


CURATED = [
    StoryParams(setting="city_block", detective="Mina", detective_gender="girl", partner="Jay", partner_gender="boy",
                clue="violet_scarf", case="missing_note", reveal="community_bulletin"),
    StoryParams(setting="library", detective="Nova", detective_gender="girl", partner="Tess", partner_gender="girl",
                clue="brass_button", case="borrowed_pen", reveal="kind_note"),
    StoryParams(setting="park", detective="Ari", detective_gender="boy", partner="Kai", partner_gender="boy",
                clue="muddy_print", case="lost_key", reveal="lost_and_found"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world's ASP twin is minimal; use --verify or --show-asp.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
