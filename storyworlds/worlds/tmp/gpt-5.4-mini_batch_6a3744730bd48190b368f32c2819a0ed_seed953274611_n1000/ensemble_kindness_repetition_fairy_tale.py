#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ensemble_kindness_repetition_fairy_tale.py
===========================================================================

A tiny fairy-tale storyworld about an ensemble of woodland friends who must
keep practicing a repeating kindness song until a shy companion can join in.

Premise:
- A small ensemble is preparing to sing at the Moon Gate.
- One member feels shy or stuck.
- The others respond with kindness, repeating a gentle refrain and helping the
  shy one try again.
- The ending image shows the ensemble singing together in a changed state.

This world is self-contained and uses the shared Storyweavers result containers
and ASP helper API.
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
KIND_MIN = 2
REPEAT_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "princess", "woman"}
        male = {"boy", "father", "king", "prince", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    magic_name: str
    opening: str
    ending: str


@dataclass
class Ensemble:
    id: str
    title: str
    refrain: str
    action: str
    stage: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShyProblem:
    id: str
    label: str
    stuck_word: str
    fear_word: str
    need_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KindResponse:
    id: str
    label: str
    method: str
    repeat_line: str
    success_line: str
    tags: set[str] = field(default_factory=set)


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
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["kindness"] < THRESHOLD:
            continue
        sig = ("soften", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hope"] += 1
        out.append("")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    singer = world.get("lead") if "lead" in world.entities else None
    if not singer:
        return out
    if singer.meters["tries"] < REPEAT_MIN:
        return out
    sig = ("repetition", singer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    singer.memes["steady"] += 1
    out.append("")
    return out


CAUSAL_RULES = [Rule("soften", "emotional", _r_soften), Rule("repetition", "emotional", _r_repetition)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def reasonable_combo(ensemble: Ensemble, problem: ShyProblem, response: KindResponse) -> bool:
    return "kindness" in ensemble.tags and "shy" in problem.tags and "repeat" in response.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for eid, ens in ENSEMBLES.items():
            for pid, prob in PROBLEMS.items():
                for rid, resp in RESPONSES.items():
                    if reasonable_combo(ens, prob, resp):
                        combos.append((sid, eid, pid, rid))
    return combos


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def setup(world: World, setting: Setting, ensemble: Ensemble, problem: ShyProblem,
          response: KindResponse, names: list[str], gender: str) -> None:
    lead = world.add(Entity(id="lead", kind="character", type=gender, label=names[0], role="lead"))
    friend = world.add(Entity(id="friend", kind="character", type="girl" if gender == "boy" else "boy",
                              label=names[1], role="friend"))
    helper = world.add(Entity(id="helper", kind="character", type="girl", label=names[2], role="helper"))
    moon = world.add(Entity(id="moon", kind="thing", label="the moon gate"))
    lead.meters["tries"] = 1
    lead.memes["shy"] = 1
    friend.memes["kindness"] = 1
    helper.memes["kindness"] = 1
    world.facts.update(setting=setting, ensemble=ensemble, problem=problem, response=response,
                       lead=lead, friend=friend, helper=helper, moon=moon)


def tell(setting: Setting, ensemble: Ensemble, problem: ShyProblem, response: KindResponse,
         lead_name: str, lead_gender: str, friend_name: str, helper_name: str) -> World:
    world = World()
    setup(world, setting, ensemble, problem, response, [lead_name, friend_name, helper_name], lead_gender)
    lead = world.get("lead")
    friend = world.get("friend")
    helper = world.get("helper")

    world.say(f"{setting.opening} {ensemble.title} gathered at {setting.place}.")
    world.say(f"They were a little ensemble, and their song began with a soft repeat: “{ensemble.refrain}”")
    world.say(f"But {lead.label_word} stood at {ensemble.stage} and felt {problem.fear_word}; {problem.stuck_word} kept {lead.pronoun('object')} from singing.")
    world.para()

    lead.memes["fear"] += 1
    friend.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    world.say(f"{friend.label_word} smiled kindly and said, “{response.repeat_line}”")
    world.say(f"Then {helper.label_word} moved closer and said it again, more gently: “{response.repeat_line}”")
    lead.meters["tries"] += 1
    lead.meters["tries"] += 1
    propagate(world)

    world.para()
    lead.memes["kindness"] += 1
    lead.meters["tries"] += 1
    world.say(f"{lead.label_word} tried once, then again, and the friends kept the kindness going: “{ensemble.refrain}”")
    world.say(f"At last, {response.method} helped {lead.label_word} breathe and join the tune.")
    lead.memes["hope"] += 1
    friend.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"{response.success_line} {setting.ending}")
    world.say(f"The little ensemble sang as one, and the moon listened like a silver lamp.")
    world.facts["outcome"] = "joined"
    return world


SETTINGS = {
    "moon_garden": Setting(
        id="moon_garden",
        place="the moon garden",
        magic_name="moon garden",
        opening="At twilight,",
        ending="The gate opened with a tiny chime, and the lanterns shone softly.",
    ),
    "rose_bridge": Setting(
        id="rose_bridge",
        place="the rose bridge",
        magic_name="rose bridge",
        opening="Near bedtime,",
        ending="The bridge glowed with warm pink light, as if it had been smiling all along.",
    ),
    "apple_hall": Setting(
        id="apple_hall",
        place="the apple hall",
        magic_name="apple hall",
        opening="On a quiet evening,",
        ending="The hall filled with golden light, and the apples on the table seemed to applaud.",
    ),
}

ENSEMBLES = {
    "forest_trio": Ensemble(
        id="forest_trio",
        title="a little forest trio",
        refrain="Soft step, kind step, try again",
        action="sing",
        stage="the mossy stump",
        tags={"kindness", "ensemble", "repeat"},
    ),
    "morrow_choir": Ensemble(
        id="morrow_choir",
        title="a small morning choir",
        refrain="One more note, one more note, together",
        action="sing",
        stage="the bright stone",
        tags={"kindness", "ensemble", "repeat"},
    ),
    "briar_band": Ensemble(
        id="briar_band",
        title="a bright briar band",
        refrain="Easy now, easy now, we can try",
        action="sing",
        stage="the ivy arch",
        tags={"kindness", "ensemble", "repeat"},
    ),
}

PROBLEMS = {
    "stage_fear": ShyProblem(
        id="stage_fear",
        label="stage fear",
        stuck_word="their tongue felt stuck",
        fear_word="shyness",
        need_word="a little courage",
        tags={"shy"},
    ),
    "forgot_words": ShyProblem(
        id="forgot_words",
        label="forgotten words",
        stuck_word="the words hid away",
        fear_word="worry",
        need_word="patient help",
        tags={"shy"},
    ),
    "shaking_voice": ShyProblem(
        id="shaking_voice",
        label="a shaking voice",
        stuck_word="their voice wobbled",
        fear_word="nervousness",
        need_word="gentle patience",
        tags={"shy"},
    ),
}

RESPONSES = {
    "repeat_kindly": KindResponse(
        id="repeat_kindly",
        label="repeat kindly",
        method="repeating the gentle line",
        repeat_line="You can do it, dear friend",
        success_line="The repeat grew steadier and warmer until the shy voice found its place.",
        tags={"repeat", "kindness"},
    ),
    "sing_again": KindResponse(
        id="sing_again",
        label="sing again",
        method="singing it again and again",
        repeat_line="Let's sing it again together",
        success_line="Again and again, the tune grew brave enough for everyone to follow.",
        tags={"repeat", "kindness"},
    ),
    "slow_breaths": KindResponse(
        id="slow_breaths",
        label="slow breaths",
        method="sharing slow breaths and repeating the first line",
        repeat_line="Breathe with us and try the first line",
        success_line="The slow breaths settled the room, and the song came out clear at last.",
        tags={"repeat", "kindness"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nina", "Tessa", "Elin", "Sera", "Lily", "Anya"]
BOY_NAMES = ["Finn", "Oren", "Milo", "Bram", "Rowan", "Ezra", "Pip", "Theo"]
CURATED = [
    StoryParams(
        setting="moon_garden",
        ensemble="forest_trio",
        problem="stage_fear",
        response="repeat_kindly",
        lead_name="Lina",
        lead_gender="girl",
        friend_name="Finn",
        helper_name="Mira",
        seed=1,
    ),
    StoryParams(
        setting="rose_bridge",
        ensemble="morrow_choir",
        problem="forgot_words",
        response="sing_again",
        lead_name="Theo",
        lead_gender="boy",
        friend_name="Nina",
        helper_name="Elin",
        seed=2,
    ),
    StoryParams(
        setting="apple_hall",
        ensemble="briar_band",
        problem="shaking_voice",
        response="slow_breaths",
        lead_name="Milo",
        lead_gender="boy",
        friend_name="Lily",
        helper_name="Sera",
        seed=3,
    ),
]


@dataclass
class StoryParams:
    setting: str
    ensemble: str
    problem: str
    response: str
    lead_name: str
    lead_gender: str
    friend_name: str
    helper_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ensemble": [("What is an ensemble?",
                  "An ensemble is a group of people who do something together, like sing or play music.")],
    "kindness": [("What is kindness?",
                  "Kindness is when someone is gentle, helpful, and caring toward another person.")],
    "repeat": [("What does repetition mean?",
                "Repetition means doing or saying something again and again.")],
    "song": [("What is a song?",
              "A song is music made with words or sounds that people can sing together.")],
    "moon": [("Why do fairy tales like the moon?",
             "The moon often feels magical in fairy tales, because it lights the night and makes the world seem quiet and strange.")],
}


def valid_settings() -> list[str]:
    return sorted(SETTINGS)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ens: Ensemble = f["ensemble"]
    prob: ShyProblem = f["problem"]
    resp: KindResponse = f["response"]
    return [
        f'Write a fairy-tale story that includes the word "ensemble" and shows a little group helping a shy singer.',
        f"Tell a child-friendly story where {f['lead'].label_word} feels {prob.fear_word}, but the ensemble keeps repeating {ens.refrain!r} until the singing feels kind and brave.",
        f"Write a gentle fairy tale about an ensemble that uses kindness and repetition to help someone join the song.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    lead: Entity = f["lead"]
    friend: Entity = f["friend"]
    helper: Entity = f["helper"]
    ens: Ensemble = f["ensemble"]
    prob: ShyProblem = f["problem"]
    resp: KindResponse = f["response"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {lead.label_word}, {friend.label_word}, and {helper.label_word}, who are part of a small ensemble at {setting.place}.",
        ),
        QAItem(
            question="What problem did the lead have?",
            answer=f"{lead.label_word} had {prob.label}, so {lead.pronoun('possessive')} voice and feelings needed kind help before the song could finish.",
        ),
        QAItem(
            question="How did the others help?",
            answer=f"They repeated {ens.refrain!r} and used {resp.label} to help {lead.label_word} feel safe enough to try again. Their kindness made the repeated line feel warmer each time.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The ensemble sang together at the end, and {lead.label_word} joined in instead of standing alone. The fairy-tale ending shows that kindness and repetition changed the whole scene.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"ensemble", "kindness", "repeat", "song", "moon"}
    out: list[QAItem] = []
    for tag in tags:
        if tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
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
    for e in world.entities.values():
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(setting: Setting, ensemble: Ensemble, problem: ShyProblem, response: KindResponse,
         lead_name: str, lead_gender: str, friend_name: str, helper_name: str) -> World:
    world = World()
    lead = world.add(Entity(id="lead", kind="character", type=lead_gender, label=lead_name, role="lead"))
    friend = world.add(Entity(id="friend", kind="character", type="boy" if lead_gender == "girl" else "girl",
                              label=friend_name, role="friend"))
    helper = world.add(Entity(id="helper", kind="character", type="girl", label=helper_name, role="helper"))
    stage = world.add(Entity(id="stage", kind="thing", label=ensemble.stage))
    lead.meters["tries"] = 1
    lead.memes["shy"] = 1
    friend.memes["kindness"] = 1
    helper.memes["kindness"] = 1
    world.facts.update(setting=setting, ensemble=ensemble, problem=problem, response=response,
                       lead=lead, friend=friend, helper=helper, stage=stage)
    world.say(f"{setting.opening} {ensemble.title} gathered at {setting.place}.")
    world.say(f"They sang the same soft refrain again and again: “{ensemble.refrain}.”")
    world.say(f"But {lead.label_word} felt {problem.fear_word}, and {problem.stuck_word} before the song could begin.")
    world.para()
    world.say(f"{friend.label_word} answered with kindness: “{response.repeat_line}”")
    world.say(f"{helper.label_word} nodded and said it once more: “{response.repeat_line}”")
    lead.meters["tries"] += 2
    lead.memes["kindness"] += 1
    world.para()
    world.say(f"{lead.label_word} took a breath, then tried again, and again, while the others kept the rhythm gentle.")
    world.say(f"At last, {response.success_line}")
    lead.memes["hope"] += 1
    friend.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"{setting.ending} {lead.label_word} sang with the ensemble, and the night felt bright and kind.")
    world.facts["outcome"] = "joined"
    return world


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, ens in ENSEMBLES.items():
        for pid, prob in PROBLEMS.items():
            for rid, resp in RESPONSES.items():
                if reasonable_combo(ens, prob, resp):
                    combos.append(("moon_garden", sid, pid, rid))
                    combos.append(("rose_bridge", sid, pid, rid))
                    combos.append(("apple_hall", sid, pid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about an ensemble, kindness, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--ensemble", choices=ENSEMBLES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--lead-name")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--helper-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    ensemble = args.ensemble or rng.choice(list(ENSEMBLES))
    problem = args.problem or rng.choice(list(PROBLEMS))
    response = args.response or rng.choice(list(RESPONSES))
    if not reasonable_combo(ENSEMBLES[ensemble], PROBLEMS[problem], RESPONSES[response]):
        raise StoryError("This combination does not support a kind, repeating fairy-tale ending.")
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or choose_name(rng, lead_gender)
    friend_name = args.friend_name or choose_name(rng, "boy" if lead_gender == "girl" else "girl")
    helper_name = args.helper_name or choose_name(rng, "girl")
    return StoryParams(setting=setting, ensemble=ensemble, problem=problem, response=response,
                       lead_name=lead_name, lead_gender=lead_gender,
                       friend_name=friend_name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.ensemble not in ENSEMBLES or params.problem not in PROBLEMS or params.response not in RESPONSES:
        raise StoryError("Unknown ensemble, problem, or response.")
    world = tell(SETTINGS[params.setting], ENSEMBLES[params.ensemble], PROBLEMS[params.problem], RESPONSES[params.response],
                 params.lead_name, params.lead_gender, params.friend_name, params.helper_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(i.question, i.answer) for i in story_qa(world)]],
        world_qa=[QAItem(q, a) for q, a in [(i.question, i.answer) for i in world_knowledge_qa(world)]],
        world=world,
    )


ASP_RULES = r"""
kind_world(E) :- ensemble(E).
repeat_world(R) :- response(R).
problem_world(P) :- problem(P).

valid(S,E,P,R) :- setting(S), ensemble(E), problem(P), response(R), kind_tag(E), shy_tag(P), repeat_tag(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for eid, e in ENSEMBLES.items():
        lines.append(asp.fact("ensemble", eid))
        lines.append(asp.fact("kind_tag", eid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("shy_tag", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("repeat_tag", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print("OK: verify passed, ASP matches Python, and a sample story generated.")
        return 0
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection() -> str:
    return "(No story: this world only tells fairy tales where kindness and repetition help someone join the ensemble.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t}" for t in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
