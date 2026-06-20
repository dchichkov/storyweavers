#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/questionnaire_suspense_humor_heartwarming.py
=============================================================================

A small story world about a child, a nervous questionnaire, a funny mystery,
and a warm ending. The core premise is simple: someone must fill out a
questionnaire, the answers matter, and the family is trying to keep a surprise
kind while the suspense builds.

The domain uses physical meters and emotional memes, forward-driven causal
state, a Python reasonableness gate, and an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/questionnaire_suspense_humor_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/questionnaire_suspense_humor_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/questionnaire_suspense_humor_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/questionnaire_suspense_humor_heartwarming.py --trace
    python storyworlds/worlds/gpt-5.4-mini/questionnaire_suspense_humor_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4-mini/questionnaire_suspense_humor_heartwarming.py --verify
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    hiding_spot: str
    reveal_spot: str
    sound: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Questionnaire:
    id: str
    title: str
    topic: str
    clue: str
    suspense_line: str
    joke_line: str
    answer_need: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    joy: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    method: str
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_anxiety(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["secret"] < THRESHOLD:
            continue
        sig = ("anxiety", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["anxiety"] += 1
        out.append("")
    return out


def _r_laughter(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["giggle"] < THRESHOLD:
            continue
        sig = ("laughter", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] += 1
        out.append("")
    return out


CAUSAL_RULES = [Rule("anxiety", "social", _r_anxiety), Rule("laughter", "social", _r_laughter)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if s])
    if narrate:
        for s in produced:
            world.say(s)


def reasonableness_ok(questionnaire: Questionnaire, prize: Prize) -> bool:
    return questionnaire.topic in {"gift", "birthday", "pet", "surprise"} and prize.id in {"giftbox", "cookies", "puppy_poster"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def choose_finish(response: Response, questionnaire: Questionnaire) -> str:
    return response.text.replace("{questionnaire}", questionnaire.title)


def predict(world: World, questionnaire: Questionnaire) -> dict:
    sim = world.copy()
    q = sim.get("child")
    q.meters["secret"] += 1
    propagate(sim, narrate=False)
    return {"anxiety": q.memes["anxiety"], "joy": q.memes["joy"]}


def introduce(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"On a quiet afternoon, {child.id} and {adult.id} sat at {setting.place}. "
        f"The whole room felt {setting.mood}, like it was waiting to whisper a secret."
    )


def show_questionnaire(world: World, child: Entity, qn: Questionnaire) -> None:
    child.meters["secret"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} found a questionnaire on the table. It asked plain little questions, "
        f"but the blank lines made {child.pronoun('possessive')} eyebrows rise."
    )
    world.say(
        f'The top line said, "{qn.title}." The next line promised a clue, '
        f'and somehow that made the paper feel more mysterious than a locked cookie jar.'
    )


def suspense_beats(world: World, child: Entity, adult: Entity, qn: Questionnaire, setting: Setting) -> None:
    world.say(
        f"{qn.suspense_line} Behind the stack of books, something rustled near {setting.hiding_spot}."
    )
    world.say(
        f'{adult.id} pretended not to notice. "{qn.joke_line}" {adult.pronoun()} said, '
        f"which did not help {child.id} at all."
    )


def warn_and_choose(world: World, child: Entity, adult: Entity, qn: Questionnaire, prize: Prize, response: Response) -> None:
    pred = predict(world, qn)
    world.facts["pred"] = pred
    world.say(
        f"{adult.id} pointed to the questionnaire and said, "
        f'"If we rush, we might forget the answer that matters most: {qn.answer_need}."'
    )
    if pred["anxiety"] >= THRESHOLD:
        world.say(f"{child.id} took a deep breath and listened.")
    child.meters["giggle"] += 1
    world.say(
        f"Then {adult.id} offered a better plan: {response.method}. "
        f"It sounded careful, kind, and just a little funny."
    )


def solve(world: World, child: Entity, adult: Entity, qn: Questionnaire, prize: Prize, response: Response) -> None:
    child.meters["secret"] = 0
    child.memes["relief"] += 1
    adult.memes["relief"] += 1
    world.say(
        f'Together they filled out the {qn.title}, and the last answer made everything click.'
    )
    world.say(
        f"{choose_finish(response, qn)}. {adult.id} smiled, and the mystery turned into a warm little laugh."
    )
    world.say(
        f"By the end, {prize.joy} felt safe in the room, and {child.id} knew the surprise was not a trick at all."
    )


def tell(setting: Setting, qn: Questionnaire, prize: Prize, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         adult_name: str = "Mom", adult_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    world.add(Entity(id="questionnaire", type="thing", label=qn.title))
    world.add(Entity(id=prize.id, type="thing", label=prize.label))
    introduce(world, child, adult, setting)
    world.para()
    show_questionnaire(world, child, qn)
    suspense_beats(world, child, adult, qn, setting)
    world.para()
    warn_and_choose(world, child, adult, qn, prize, response)
    solve(world, child, adult, qn, prize, response)
    world.facts.update(child=child, adult=adult, setting=setting, questionnaire=qn, prize=prize, response=response)
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "bright and busy", "the breadbox", "the counter", "a spoon tapped against a bowl", tags={"home"}),
    "living_room": Setting("living_room", "the living room", "cozy and quiet", "the sofa pillow", "the lamp table", "the clock gave one tiny tick", tags={"home"}),
    "porch": Setting("porch", "the porch", "cool and breezy", "the flower pot", "the mail basket", "the wind made a soft whoosh", tags={"home"}),
}

QUESTIONNAIRES = {
    "gift": Questionnaire("gift", "Grandma's Surprise Questionnaire", "gift", "a hidden ribbon under the paper",
                          "One answer was missing, and that missing line felt louder than a drum.", "maybe the paper was asking to be fed cookies",
                          "choose a gift that would make Grandma smile", tags={"questionnaire", "gift"}),
    "birthday": Questionnaire("birthday", "Birthday Helper Questionnaire", "birthday", "a confetti sticker on the back",
                               "The last question was covered by a sticky note, and nobody would say why.", "the sticky note looked like it was guarding treasure",
                               "pick the kindest surprise for the party", tags={"questionnaire", "birthday"}),
    "pet": Questionnaire("pet", "Pet Day Questionnaire", "pet", "a paw print doodle in the corner",
                          "A small paw print seemed to point toward a secret answer.", "even the doodle looked too proud to spill the beans",
                          "find what would make the pet feel calm and happy", tags={"questionnaire", "pet"}),
}

PRIZES = {
    "giftbox": Prize("giftbox", "a wrapped gift box", "a wrapped gift box", "the gift would feel ready", tags={"gift"}),
    "cookies": Prize("cookies", "a plate of cookies", "a plate of cookies", "the cookies would feel loved", plural=True, tags={"gift"}),
    "puppy_poster": Prize("puppy_poster", "a puppy poster", "a puppy poster", "the poster would make the room cheer up", tags={"pet"}),
}

RESPONSES = {
    "peek": Response("peek", 2, "peeked under the ribbon", "looked under the ribbon and found the answer hiding there", "peeked under the ribbon and found the answer"),
    "ask": Response("ask", 3, "asked the grown-up a careful question", "asked one careful question and got the missing clue", "asked a careful question and got the missing clue"),
    "wait": Response("wait", 3, "waited for the surprise to be explained", "waited, which gave the secret enough time to become funny instead of scary", "waited for the secret to become funny"),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    questionnaire: str
    prize: str
    response: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for qid, qn in QUESTIONNAIRES.items():
            for pid, prize in PRIZES.items():
                if reasonableness_ok(qn, prize):
                    combos.append((sid, qid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming suspense-and-humor story world about a questionnaire.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--questionnaire", choices=QUESTIONNAIRES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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


def _pick(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.questionnaire and args.prize:
        qn, pr = QUESTIONNAIRES[args.questionnaire], PRIZES[args.prize]
        if not reasonableness_ok(qn, pr):
            raise StoryError("That questionnaire and prize do not make a believable suspense story together.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.questionnaire is None or c[1] == args.questionnaire)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, qid, pid = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(["Mia", "Noah", "Lena", "Theo", "Iris", "Owen"])
    adult = args.adult or ("Mom" if adult_gender == "woman" else "Dad")
    return StoryParams(setting, qid, pid, response, child, child_gender, adult, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTIONNAIRES[params.questionnaire], PRIZES[params.prize], RESPONSES[params.response],
                 params.child, params.child_gender, params.adult, params.adult_gender)
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the word "questionnaire" and a small mystery.',
        f"Tell a suspenseful but funny story where {f['child'].id} finds {f['questionnaire'].title} and worries about the hidden clue.",
        f"Write a gentle family story about answering {f['questionnaire'].title} together, with a warm ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    qn = f["questionnaire"]
    prize = f["prize"]
    resp = f["response"]
    return [
        ("What did the child find?", f"{child.id} found {qn.title}. The paper seemed ordinary at first, but the hidden clue made it feel secret."),
        ("Why was the child worried?", f"{child.id} worried because one answer was missing and nobody would explain it right away. That suspense made the questionnaire seem almost like a mystery."),
        ("How did they solve it?", f"{adult.id} helped by {resp.qa_text}, and then they filled in the last answer together. The mystery turned into a kind, funny moment."),
        ("How did the story end?", f"It ended warmly, with {prize.joy} and a calm feeling in the room. {child.id} learned that a surprise can be safe and loving too."),
    ]


WORLD_KNOWLEDGE = {
    "questionnaire": [("What is a questionnaire?", "A questionnaire is a page of questions that asks you to answer things about a topic. People use it to learn what someone likes or needs.")],
    "surprise": [("What is a surprise?", "A surprise is something you do not know about ahead of time. A good surprise should still feel kind and safe.")],
    "secret": [("Why do secrets feel suspenseful?", "Secrets can feel suspenseful because you know something important is hidden. Waiting to learn it can make your heart beat faster.")],
    "laugh": [("Why can funny moments help with suspense?", "A funny moment can make worry feel smaller and help everyone relax. That is why a joke can turn a scary feeling into a safe one.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    for tag in ["questionnaire", "surprise", "secret", "laugh"]:
        out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "gift", "giftbox", "ask", "Mia", "girl", "Mom", "woman"),
    StoryParams("living_room", "birthday", "cookies", "wait", "Noah", "boy", "Dad", "man"),
    StoryParams("porch", "pet", "puppy_poster", "peek", "Iris", "girl", "Mom", "woman"),
]


def explain_rejection(qn: Questionnaire, prize: Prize) -> str:
    return f"(No story: {qn.title} and {prize.label} do not make a believable questionnaire mystery.)"


def outcome_of(params: StoryParams) -> str:
    return "warm"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTIONNAIRES.items():
        lines.append(asp.fact("questionnaire", qid))
        lines.append(asp.fact("topic", qid, q.topic))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,P) :- setting(S), questionnaire(Q), prize(P), topic(Q, T), prize(P), allowed(T, P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print()
        for s, q, p in asp_valid_combos():
            print(f"{s:12} {q:18} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.questionnaire} / {p.prize} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
