#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/village_tipsy_bad_ending_teamwork_superhero_story.py
===================================================================================

A standalone storyworld for a small superhero village tale with teamwork, a bad
ending, and the seed words "village" and "tipsy".

Premise
-------
A tiny village has a cheerful team of little heroes. They try to work together
to stop a wobbling menace, but their plan is too late and the village ends up
damaged. The ending is sad, but the teamwork is real and visible in the world
state.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a forward-chained world model
- generation prompts, story QA, and world-knowledge QA from simulated state
- a Python reasonableness gate and an inline ASP twin
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
TEAMWORK_MIN = 2.0


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    village_name: str
    scene: str
    trouble: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HeroCfg:
    id: str
    type: str
    label: str
    power: str
    helper: str
    courage: int
    teamwork: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ThreatCfg:
    id: str
    label: str
    phrase: str
    wobble: str
    can_fall: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ResponseCfg:
    id: str
    text: str
    teamwork_need: int
    power: int
    fail_text: str
    qa_text: str
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["danger"] >= THRESHOLD and ("alarm", e.id) not in world.fired:
            world.fired.add(("alarm", e.id))
            for h in world.entities.values():
                if h.role == "hero":
                    h.memes["fear"] += 1
            out.append("__alarm__")
    return out


def _r_collapse(world: World) -> list[str]:
    out: list[str] = []
    tower = world.entities.get("tower")
    if not tower or tower.meters["wobble"] < THRESHOLD:
        return out
    if ("collapse", "tower") in world.fired:
        return out
    world.fired.add(("collapse", "tower"))
    tower.meters["broken"] = 1
    if "square" in world.entities:
        world.get("square").meters["damage"] += 1
    out.append("__collapse__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm), Rule("collapse", "physical", _r_collapse)]


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


def valid_response(r: ResponseCfg, teamwork: int) -> bool:
    return teamwork >= r.teamwork_need


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hero in HEROES:
            for threat in THREATS:
                if setting == "village" and threat == "tower":
                    combos.append((setting, hero, threat))
    return combos


def reasonableness_gate(setting: Setting, threat: ThreatCfg) -> bool:
    return setting.id == "village" and threat.can_fall


def predict_bad(world: World, threat_id: str) -> bool:
    sim = world.copy()
    sim.get(threat_id).meters["wobble"] += 1
    propagate(sim, narrate=False)
    return sim.get(threat_id).meters["broken"] >= THRESHOLD


def _do_plan(world: World, heroes: list[Entity], threat: Entity, resp: ResponseCfg) -> None:
    for h in heroes:
        h.memes["teamwork"] += 1
    threat.meters["wobble"] += 1
    if resp.power >= 2:
        threat.meters["stopped"] += 0.5
    propagate(world, narrate=False)


def tell(setting: Setting, hero1: HeroCfg, hero2: HeroCfg, threat: ThreatCfg,
         response: ResponseCfg, seed_word: str = "tipsy") -> World:
    world = World()
    square = world.add(Entity(id="square", kind="place", type="place", label="the square"))
    tower = world.add(Entity(id="tower", kind="thing", type="thing", label=threat.label))
    h1 = world.add(Entity(id=hero1.id, kind="character", type=hero1.type, label=hero1.label,
                          role="hero", traits=["brave", "helpful"], attrs={"power": hero1.power}))
    h2 = world.add(Entity(id=hero2.id, kind="character", type=hero2.type, label=hero2.label,
                          role="hero", traits=["quick", "kind"], attrs={"power": hero2.power}))
    h1.memes["teamwork"] = hero1.teamwork
    h2.memes["teamwork"] = hero2.teamwork
    h1.memes["courage"] = hero1.courage
    h2.memes["courage"] = hero2.courage
    world.facts["setting"] = setting
    world.facts["seed_word"] = seed_word

    world.say(
        f"In the village of {setting.village_name}, {h1.id} and {h2.id} wore bright capes "
        f"and watched over the square. Everyone called them the team because they always tried to help."
    )
    world.say(
        f"One evening, the {threat.label_word} began to {threat.wobble}, and the whole village looked tipsy."
    )

    world.para()
    h1.memes["hope"] += 1
    h2.memes["hope"] += 1
    world.say(
        f'"We can fix it together," said {h1.id}. "{h2.id}, take the left side and I will take the right."'
    )
    world.say(
        f"They rushed in as a team, but the plan was too small for the big wobble."
    )

    world.para()
    h1.meters["effort"] += 1
    h2.meters["effort"] += 1
    threat.meters["wobble"] += 1
    world.say(
        f"{h1.id} and {h2.id} pushed and pulled, using all their teamwork. "
        f"They even tied a rope around {threat.label_word}, but the rope slipped on the stones."
    )
    world.say(
        f"Then the {threat.label_word} gave a terrible shiver."
    )

    danger_now = predict_bad(world, "tower")
    world.get("tower").meters["wobble"] = 1
    propagate(world, narrate=False)

    world.para()
    if danger_now:
        world.get("square").meters["damage"] += 2
        world.get("tower").meters["broken"] = 1
        world.say(
            f"{response.fail_text}. The {threat.label_word} tipped over anyway and crashed through the flower cart."
        )
        world.say(
            f"The heroes did their best side by side, but the village ended up muddy, noisy, and sad."
        )
        world.say(
            f"By morning, the square was broken, and the people of the village could only sweep up the pieces and sigh."
        )
    else:
        world.say(
            f"{response.text}. The {threat.label_word} steadied, and the village cheered."
        )
        world.say(
            f"But this world wanted a bad ending, so the broken stones still showed where the trouble had been."
        )

    world.facts.update(
        heroes=(h1, h2),
        threat=world.get("tower"),
        response=response,
        outcome="bad",
    )
    return world


SETTINGS = {
    "village": Setting(
        id="village",
        village_name="Brindle",
        scene="a little market square with red roofs",
        trouble="the wind around the bell tower",
        tags={"village"},
    )
}

HEROES = {
    "spark": HeroCfg(
        id="Spark",
        type="boy",
        label="Spark",
        power="fast hands",
        helper="a bright rope",
        courage=7,
        teamwork=5,
        tags={"hero"},
    ),
    "beam": HeroCfg(
        id="Beam",
        type="girl",
        label="Beam",
        power="steady feet",
        helper="a strong shield",
        courage=6,
        teamwork=6,
        tags={"hero"},
    ),
}

THREATS = {
    "tower": ThreatCfg(
        id="tower",
        label="bell tower",
        phrase="the old bell tower",
        wobble="wobble like a sleepy giant",
        can_fall=True,
        tags={"tower", "tipsy"},
    )
}

RESPONSES = {
    "rope_team": ResponseCfg(
        id="rope_team",
        text="Together they wrapped the rope around the tower and braced their feet",
        teamwork_need=2,
        power=1,
        fail_text="They pulled with all their hearts, but not hard enough",
        qa_text="wrapped the rope around the tower and braced it together",
        tags={"teamwork"},
    ),
    "shield_push": ResponseCfg(
        id="shield_push",
        text="Beam held the shield while Spark pushed from behind",
        teamwork_need=2,
        power=1,
        fail_text="They held the shield and pushed, but the tower still tilted",
        qa_text="held the shield and pushed together",
        tags={"teamwork"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    hero1: str
    hero2: str
    threat: str
    response: str
    seed_word: str = "tipsy"
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="village", hero1="spark", hero2="beam", threat="tower", response="rope_team", seed_word="tipsy"),
    StoryParams(setting="village", hero1="beam", hero2="spark", threat="tower", response="shield_push", seed_word="tipsy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero village storyworld with teamwork and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero1", choices=HEROES)
    ap.add_argument("--hero2", choices=HEROES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and not valid_response(RESPONSES[args.response], 2):
        raise StoryError("Chosen response is not reasonable for this teamwork story.")
    setting = args.setting or "village"
    hero1 = args.hero1 or rng.choice(list(HEROES))
    hero2 = args.hero2 or rng.choice([h for h in HEROES if h != hero1])
    threat = args.threat or "tower"
    response = args.response or rng.choice(list(RESPONSES))
    if not reasonableness_gate(SETTINGS[setting], THREATS[threat]):
        raise StoryError("This setting and threat do not form a reasonable village hazard.")
    return StoryParams(setting=setting, hero1=hero1, hero2=hero2, threat=threat, response=response, seed_word="tipsy")


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a superhero story that includes the words "village" and "tipsy".',
        "Tell a teamwork story about two little heroes trying to save their village, but the ending goes badly.",
        "Write a child-friendly superhero tale where helpers work together, yet the village is still damaged in the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h1, h2 = world.facts["heroes"]
    threat = world.facts["threat"]
    return [
        QAItem(
            question="Who are the story heroes?",
            answer=f"The story is about {h1.id} and {h2.id}, two tiny heroes who tried to help their village.",
        ),
        QAItem(
            question="What did they try to save?",
            answer=f"They tried to save the village square from the wobbling {threat.label_word}. They worked together, but the trouble was bigger than their plan.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly. The tower fell, the square was damaged, and the village had to clean up the mess the next morning.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a village?",
            answer="A village is a small place where people live close together. It often has a square, homes, and neighbors who know one another.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work as one team. They share the job so the work is easier.",
        ),
        QAItem(
            question="What does tipsy mean?",
            answer="Tipsy means wobbly or unsteady, like something that might tip over. In a story, it can make trouble feel shaky and unsafe.",
        ),
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.hero1 not in HEROES or params.hero2 not in HEROES:
        raise StoryError("Invalid StoryParams for this world.")
    world = tell(SETTINGS[params.setting], HEROES[params.hero1], HEROES[params.hero2], THREATS[params.threat], RESPONSES[params.response], params.seed_word)
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


ASP_RULES = r"""
danger(X) :- wobble(X).
broken(X) :- danger(X), can_fall(X).
outcome(bad) :- broken(tower).
teamwork_ok(H1,H2) :- hero(H1), hero(H2), H1 != H2.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        if t.can_fall:
            lines.append(asp.fact("can_fall", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show hero/1.\n#show threat/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    rc = 0
    try:
        python_gate = set(valid_combos())
        import asp
        model = asp.one_model(asp_program("#show setting/1.\n#show hero/1.\n#show threat/1."))
        clingo_gate = set(asp.atoms(model, "setting"))
        if not clingo_gate:
            raise RuntimeError("ASP did not produce a model")
        print("OK: ASP module loaded and produced a model.")
        print(f"OK: valid_combos() returned {len(python_gate)} combos.")
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        rc = 1
    return rc


def valid_response_ids() -> list[str]:
    return [rid for rid, r in RESPONSES.items() if r.teamwork_need <= 2]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show setting/1.\n#show hero/1.\n#show threat/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Available setting/hero/threat facts via ASP:")
        print(asp_program("#show setting/1.\n#show hero/1.\n#show threat/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
