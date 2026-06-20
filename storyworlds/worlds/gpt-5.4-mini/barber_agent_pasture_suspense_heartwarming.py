#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/barber_agent_pasture_suspense_heartwarming.py
===============================================================================

A standalone story world for a tiny heartwarming suspense tale built from the
seed words barber, agent, and pasture.

Premise:
- A child notices a missing lamb near a pasture fence.
- A barber, who also knows how to stay calm and observe details, helps.
- An agent arrives to investigate a possible clue, but the suspense resolves
  into a gentle reunion and a small act of care.

The world is intentionally small and classical: a few typed entities, a causal
state machine, a reasonableness gate, an inline ASP twin, and a renderer that
lets world state drive the prose.
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    breeze: str
    safety_image: str


@dataclass
class Role:
    id: str
    label: str
    title: str
    careful: bool = False
    makes_hair_neat: bool = False


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    near: str
    risky: bool = False


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("child").memes["suspense"] += 1
        out.append("__worry__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.entities.get("lamb") and world.get("lamb").meters["found"] >= THRESHOLD:
        sig = ("calm", "lamb")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["relief"] += 1
            if "barber" in world.entities:
                world.get("barber").memes["warmth"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("calm", "social", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(setting: Setting, role: Role, clue: Clue, response: Response) -> bool:
    return setting.id == "pasture" and role.id == "barber" and clue.risky and response.sense >= 2


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict_missing(world: World) -> dict:
    sim = world.copy()
    sim.get("child").memes["worry"] += 1
    sim.get("barber").memes["observation"] += 1
    return {
        "suspense": sim.get("child").memes["suspense"],
        "relief": sim.get("child").memes["relief"],
    }


def setup(world: World, child: Entity, barber: Entity, agent: Entity, setting: Setting) -> None:
    child.memes["love"] += 1
    barber.memes["calm"] += 1
    agent.memes["focus"] += 1
    world.say(
        f"Late in the afternoon, {child.id} stood by the {setting.label} and listened to the quiet wind."
    )
    world.say(
        f"Near the fence, {child.id} noticed a small trail in the grass and felt a worried twist in {child.pronoun('possessive')} chest."
    )


def suspense(world: World, child: Entity, barber: Entity, agent: Entity, clue: Clue) -> None:
    child.memes["worry"] += 1
    barber.memes["observation"] += 1
    world.say(
        f"A gentle suspense settled over the pasture. {child.id} pointed at {clue.phrase} and whispered that something might be missing."
    )
    world.say(
        f"{barber.id}, the barber, bent low to look at the grass. {barber.pronoun().capitalize()} said the best clues were often small and easy to miss."
    )
    world.say(
        f"Then an agent arrived with careful steps, carrying a notebook and a kind face, ready to help without frightening anyone."
    )
    propagate(world, narrate=True)


def search(world: World, barber: Entity, agent: Entity, clue: Clue) -> None:
    world.say(
        f"{agent.id} followed the tracks near {clue.near}, while {barber.id} checked the gate and the hedges."
    )
    world.say(
        f"The search stayed quiet, because nobody wanted to startle the animals in the pasture."
    )


def reveal(world: World, child: Entity, barber: Entity, agent: Entity) -> None:
    lamb = world.get("lamb")
    lamb.meters["found"] = 1.0
    lamb.memes["safe"] += 1
    child.memes["joy"] += 1
    barber.memes["warmth"] += 1
    agent.memes["approval"] += 1
    world.say(
        f"At last, {agent.id} heard a soft bleat behind the hay wagon. The missing lamb was there all along, safe and tucked in the shade."
    )
    world.say(
        f"{barber.id} smiled and helped lift a loose latch, and {child.id} hurried over with a carrot from the basket."
    )


def ending(world: World, child: Entity, barber: Entity, agent: Entity, setting: Setting) -> None:
    world.say(
        f"{child.id} laughed with relief, and the little lamb nuzzled {child.pronoun('possessive')} hand as if nothing scary had ever happened."
    )
    world.say(
        f"{barber.id} trimmed the hay-stained whiskers from {agent.pronoun('possessive')} coat, grinning at the silly work of the day."
    )
    world.say(
        f"By sunset, the pasture was peaceful again, and {child.id} walked home feeling brave, helped, and deeply glad."
    )


def tell(setting: Setting, role: Role, clue: Clue, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         barber_name: str = "Noah", barber_gender: str = "boy",
         agent_name: str = "Agent Wren", agent_gender: str = "woman") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    barber = world.add(Entity(id=barber_name, kind="character", type=barber_gender, role="barber"))
    agent = world.add(Entity(id=agent_name, kind="character", type=agent_gender, role="agent"))
    lamb = world.add(Entity(id="lamb", kind="animal", type="lamb", label="small lamb"))
    world.add(Entity(id="gate", type="thing", label="the gate"))
    world.add(Entity(id="wagon", type="thing", label="the hay wagon"))

    setup(world, child, barber, agent, setting)
    world.para()
    suspense(world, child, barber, agent, clue)
    world.para()
    search(world, barber, agent, clue)
    reveal(world, child, barber, agent)
    world.para()
    ending(world, child, barber, agent, setting)

    world.facts.update(
        child=child, barber=barber, agent=agent, lamb=lamb,
        setting=setting, role=role, clue=clue, response=response,
        outcome="found", predicted=predict_missing(world),
    )
    return world


SETTINGS = {
    "pasture": Setting("pasture", "pasture", "soft wind", "the pasture turned calm and gold"),
}

ROLES = {
    "barber": Role("barber", "barber", "the barber", careful=True, makes_hair_neat=True),
}

CLUES = {
    "missing_lamb": Clue("missing_lamb", "missing lamb", "a missing lamb", "the fence near the hay wagon", risky=True),
    "quiet_tracks": Clue("quiet_tracks", "quiet tracks", "tiny tracks in the grass", "the fence by the wagon", risky=True),
}

RESPONSES = {
    "search": Response("search", 3, 3,
                       "followed the clues until the missing lamb was found safe",
                       "looked everywhere, but the clue trail went cold",
                       "followed the clues until the missing lamb was found"),
    "listen": Response("listen", 2, 2,
                       "took a careful breath and listened for a small sound",
                       "waited too long, and the little sound was lost",
                       "listened carefully and found the answer"),
}

GIRL_NAMES = ["Mina", "Ivy", "Lena", "Rose", "Aria"]
BOY_NAMES = ["Noah", "Eli", "Owen", "Theo", "Milo"]


@dataclass
class StoryParams:
    setting: str
    role: str
    clue: str
    response: str
    child_name: str
    child_gender: str
    barber_name: str
    barber_gender: str
    agent_name: str
    agent_gender: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "barber": [("What does a barber do?",
                "A barber cuts hair and helps people keep it neat and tidy.")],
    "agent": [("What is an agent?",
               "An agent is a person who helps solve a problem or gather information carefully.")],
    "pasture": [("What is a pasture?",
                 "A pasture is a field where grass grows and animals like to graze.")],
    "lamb": [("What is a lamb?",
              "A lamb is a baby sheep. Lambs stay close to where they feel safe.")],
    "suspense": [("What is suspense in a story?",
                 "Suspense is the feeling that makes you wonder what will happen next.")],
    "heartwarming": [("What makes a story heartwarming?",
                     "A heartwarming story leaves you feeling kind, safe, and glad that people helped each other.")],
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for rid, role in ROLES.items():
            for cid, clue in CLUES.items():
                for xid, response in RESPONSES.items():
                    if reasonableness_ok(setting, role, clue, response):
                        combos.append((sid, rid, cid, xid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: barber, agent, pasture, suspense, heartwarming.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--barber-name")
    ap.add_argument("--barber-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--agent-name")
    ap.add_argument("--agent-gender", choices=["girl", "boy", "woman", "man"])
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


def explain_rejection() -> str:
    return "(No story: this combination does not make a believable suspense in the pasture.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.role is None or c[1] == args.role)
              and (args.clue is None or c[2] == args.clue)
              and (args.response is None or c[3] == args.response)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, role, clue, response = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    barber_gender = args.barber_gender or rng.choice(["boy", "man"])
    barber_name = args.barber_name or rng.choice(BOY_NAMES)
    agent_gender = args.agent_gender or rng.choice(["woman", "man"])
    agent_name = args.agent_name or "Agent Wren"
    return StoryParams(setting, role, clue, response, child_name, child_gender,
                       barber_name, barber_gender, agent_name, agent_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming suspense story for a young child that includes the words "barber", "agent", and "pasture".',
        f"Tell a gentle mystery where {f['child'].id} sees something missing in the pasture and a barber and an agent help find it.",
        f"Write a calm, suspenseful story that starts with worry in a pasture and ends with a kind reunion.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, barber, agent = f["child"], f["barber"], f["agent"]
    setting, clue = f["setting"], f["clue"]
    return [
        QAItem("Who is the story about?",
               f"It is about {child.id}, {barber.id}, and {agent.id}. The story begins with worry in the {setting.label} and ends with everyone feeling safe."),
        QAItem("Why did the story feel suspenseful?",
               f"{child.id} thought something was missing, so everyone had to look carefully before the answer was clear. The suspense came from not knowing where the small animal had gone."),
        QAItem("How did the story end?",
               f"It ended happily when the missing lamb was found safe. The pasture became peaceful again, which makes the ending heartwarming."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does a barber do?",
               KNOWLEDGE["barber"][0][1]),
        QAItem("What is an agent?",
               KNOWLEDGE["agent"][0][1]),
        QAItem("What is a pasture?",
               KNOWLEDGE["pasture"][0][1]),
        QAItem("What is suspense in a story?",
               KNOWLEDGE["suspense"][0][1]),
        QAItem("What makes a story heartwarming?",
               KNOWLEDGE["heartwarming"][0][1]),
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pasture", "barber", "missing_lamb", "search", "Mina", "girl", "Noah", "boy", "Agent Wren", "woman"),
    StoryParams("pasture", "barber", "quiet_tracks", "listen", "Owen", "boy", "Eli", "boy", "Agent Wren", "woman"),
]


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in ROLES:
        lines.append(asp.fact("role", rid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for xid, resp in RESPONSES.items():
        lines.append(asp.fact("response", xid))
        lines.append(asp.fact("sense", xid, resp.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, R, C, X) :- setting(S), role(R), clue(C), response(X),
                     S = "pasture", R = "barber", risky(C), sense(X, N), sense_min(M), N >= M.
outcome(found) :- valid(_, _, _, _).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combo sets differ.")
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ROLES[params.role], CLUES[params.clue],
                 RESPONSES[params.response], params.child_name, params.child_gender,
                 params.barber_name, params.barber_gender, params.agent_name,
                 params.agent_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
