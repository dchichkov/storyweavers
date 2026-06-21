#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/statue_glance_indoor_play_cafe_reconciliation_space.py
======================================================================================

A standalone storyworld for a tiny indoor play-cafe space adventure where a
child, a small statue, a suspicious glance, and a reconciliation all matter.

Premise:
- Two kids are playing in an indoor play cafe that feels like a little starship.
- One child makes a hasty glance at a statue and thinks the other child broke it.
- Tension rises, then a careful check reveals the statue is fine.
- The children reconcile and continue the game with a safer, kinder plan.

This script follows the shared storyworld contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- reasonableness gate plus inline ASP twin
- prompts, story QA, and world-knowledge QA derived from world state
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
SPACE_TRAITS = {"brave", "curious", "careful", "kind", "thoughtful"}


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str
    theme: str
    affordance: str


@dataclass
class Artifact:
    id: str
    label: str
    material: str
    can_chip: bool
    can_glint: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Look:
    id: str
    label: str
    risk: int
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_tension(world: World) -> list[str]:
    out = []
    if world.get("child_a").memes["hurt"] >= THRESHOLD and ("tension",) not in world.fired:
        world.fired.add(("tension",))
        world.get("child_b").memes["worry"] += 1
        world.get("cafe").meters["buzz"] += 1
        out.append("__tension__")
    return out


def _r_reassure(world: World) -> list[str]:
    out = []
    if world.get("child_b").memes["apology"] >= THRESHOLD and ("reconcile",) not in world.fired:
        world.fired.add(("reconcile",))
        world.get("child_a").memes["hurt"] = max(0.0, world.get("child_a").memes["hurt"] - 1)
        world.get("child_b").memes["worry"] = max(0.0, world.get("child_b").memes["worry"] - 1)
        world.get("child_a").memes["warmth"] += 1
        world.get("child_b").memes["warmth"] += 1
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("tension", _r_tension), Rule("reconcile", _r_reassure)]


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


def glance_risk(look: Look, artifact: Artifact) -> bool:
    return look.kind == "sharp" and artifact.can_chip


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for lid, look in LOOKS.items():
            for aid, art in ARTIFACTS.items():
                if glance_risk(look, art):
                    combos.append((sid, lid, aid))
    return combos


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def is_contained(response: Response, artifact: Artifact, delay: int) -> bool:
    return response.power >= (artifact.risk + delay)


def predict_misread(world: World, artifact_id: str) -> dict:
    sim = world.copy()
    _nudge_artifact(sim, sim.get(artifact_id), narrate=False)
    return {"hurt": sim.get("child_a").memes["hurt"], "buzz": sim.get("cafe").meters["buzz"]}


def _nudge_artifact(world: World, artifact: Entity, narrate: bool = True) -> None:
    artifact.meters["noticed"] += 1
    world.get("child_a").memes["hurt"] += 1
    propagate(world, narrate=narrate)


def open_scene(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f"In {setting.place}, the play cafe hummed like a little launch deck. "
        f"{a.id} and {b.id} tucked their game beside a small {setting.theme}."
    )


def space_game(world: World, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"They played as if the tables were starships and the rugs were moon dust, "
        f"with {a.id} steering and {b.id} scouting ahead."
    )


def notice_statue(world: World, b: Entity, artifact: Artifact) -> None:
    world.say(
        f"Then {b.id} gave the little {artifact.label} a quick glance and frowned. "
        f'It looked as if something had gone wrong.'
    )


def blame(world: World, a: Entity, b: Entity, artifact: Artifact) -> None:
    a.memes["hurt"] += 1
    a.memes["fear"] += 1
    world.say(
        f'"Did you bump the {artifact.label}?" {a.id} asked, voice small and shaky. '
        f"{b.id} froze beside the tunnel slide."
    )


def check(world: World, helper: Entity, artifact: Artifact) -> None:
    world.say(
        f"{helper.id} knelt for a closer look. The tiny {artifact.label} had only "
        f"caught the light; it had not cracked at all."
    )


def apologize(world: World, b: Entity, a: Entity) -> None:
    b.memes["apology"] += 1
    world.say(
        f'"I am sorry," {b.id} said. "I made a bad glance and scared you. I should '
        f"have checked first.""
    )


def reconcile(world: World, a: Entity, b: Entity, artifact: Artifact, setting: Setting) -> None:
    world.say(
        f"{a.id} took a breath, then smiled a little. " 
        f'"I thought the {artifact.label} was broken," {a.id} said, '
        f'"but it was only a shiny light. We can still play."'
    )
    world.say(
        f"{b.id} smiled back, and they tapped the {artifact.label} gently as a peace "
        f"signal before flying their cardboard ship to the next station."
    )
    a.memes["warmth"] += 1
    b.memes["warmth"] += 1


def finish(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f"By the time they reached the snack counter, the whole cafe felt calm again. "
        f"{a.id} and {b.id} were side by side, ready for one more orbit around the play room."
    )


def tell(setting: Setting, artifact: Artifact, look: Look, response: Response,
         child_a: str = "Mina", child_b: str = "Ravi", parent: str = "parent",
         delay: int = 0) -> World:
    world = World()
    a = world.add(Entity(id=child_a, kind="character", type="girl", role="child"))
    b = world.add(Entity(id=child_b, kind="character", type="boy", role="child"))
    p = world.add(Entity(id=parent, kind="character", type="parent", label="the grown-up"))
    cafe = world.add(Entity(id="cafe", type="place", label=setting.place))
    art = world.add(Entity(id="artifact", type="thing", label=artifact.label, attrs={"risk": artifact.can_chip}))

    open_scene(world, a, b, setting)
    space_game(world, a, b)
    world.para()
    notice_statue(world, b, artifact)
    world.say(f"{a.id} followed {b.pronoun('possessive')} glance and started to worry.")
    blame(world, a, b, artifact)
    check(world, p, artifact)
    world.para()
    apologize(world, b, a)
    if look.kind == "sharp":
        _nudge_artifact(world, art)
    if is_contained(response, artifact, delay):
        world.say(
            f'{p.id} came over, and {response.text.replace("{artifact}", artifact.label)}.'
        )
        reconcile(world, a, b, artifact, setting)
        finish(world, a, b, setting)
    else:
        world.say(
            f'{p.id} tried to help, but {response.fail.replace("{artifact}", artifact.label)}.'
        )
        world.say(
            f"The cafe buzzed with worry until everyone had to pause and reset the game."
        )
    world.facts.update(
        child_a=a, child_b=b, parent=p, setting=setting, artifact=artifact,
        look=look, response=response, delay=delay,
        reconciled=bool(b.memes["apology"] >= THRESHOLD),
        tension=a.memes["hurt"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "cafe": Setting(id="cafe", place="the indoor play cafe", theme="space station", affordance="play"),
    "corner": Setting(id="corner", place="the sunny corner of the play cafe", theme="moon base", affordance="play"),
}

ARTIFACTS = {
    "statue": Artifact(id="statue", label="statue", material="stone", can_chip=True, can_glint=True, tags={"statue"}),
    "rocket": Artifact(id="rocket", label="rocket model", material="plastic", can_chip=False, can_glint=True, tags={"rocket"}),
}

LOOKS = {
    "glance": Look(id="glance", label="glance", risk=2, kind="sharp", tags={"glance"}),
    "peek": Look(id="peek", label="peek", risk=1, kind="soft", tags={"peek"}),
}

RESPONSES = {
    "check": Response(id="check", sense=3, power=3,
                      text="looked closely and saw that the statue was fine",
                      fail="looked closely, but the worry had already spread",
                      qa_text="looked closely and saw that the statue was fine",
                      tags={"check"}),
    "hug": Response(id="hug", sense=2, power=2,
                    text="gave a calm hug and asked everyone to breathe first",
                    fail="tried to calm things down, but the fear stayed hot",
                    qa_text="gave a calm hug and asked everyone to breathe first",
                    tags={"hug"}),
    "glowlamp": Response(id="glowlamp", sense=1, power=1,
                         text="turned on a little lamp, but that did not settle the mix-up",
                         fail="turned on a little lamp, but the mix-up was still too big",
                         qa_text="turned on a little lamp",
                         tags={"lamp"}),
}

SENSE_MIN = 2
GIRL_NAMES = ["Mina", "Lena", "Tia", "Noor", "Aya"]
BOY_NAMES = ["Ravi", "Owen", "Milo", "Kai", "Ivo"]
TRAITS = ["brave", "curious", "careful", "kind", "thoughtful"]


@dataclass
class StoryParams:
    setting: str
    artifact: str
    look: str
    response: str
    child_a: str
    child_b: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "statue": [("What is a statue?", "A statue is a carved or shaped object that stands still and is made to be looked at.")],
    "glance": [("What is a glance?", "A glance is a very quick look at something.")],
    "space": [("What is a space station?", "A space station is a place where people imagine working and living in space.")],
    "apology": [("Why do people apologize?", "People apologize when they hurt feelings or make a mistake. An apology helps start fixing things.")],
}

KNOWLEDGE_ORDER = ["statue", "glance", "space", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a space-adventure story set in an indoor play cafe that includes the words "statue" and "glance".',
        f"Tell a story where {f['child_b'].id} gives a quick glance at a statue in a play cafe, "
        f"then {f['child_a'].id} worries, and the children reconcile.",
        f"Write a gentle story in a moon-base style play cafe where a mistaken glance leads to a small conflict and then a friendly apology.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, p, art, resp = f["child_a"], f["child_b"], f["parent"], f["artifact"], f["response"]
    qa = [
        ("Where does the story take place?",
         f"It takes place in {f['setting'].place}. The indoor play cafe gives the story its space-adventure feel."),
        ("Why did the children start to worry?",
         f"{a.id} thought the statue might have been damaged after {b.id}'s glance. That mistake made the moment feel scary even though nothing was actually broken."),
        ("What fixed the problem?",
         f"The grown-up checked the statue, and {b.id} apologized. That careful check and apology helped the children calm down and reconcile."),
    ]
    if f.get("reconciled"):
        qa.append((
            "How did the story end?",
            f"It ended with the children feeling friendly again. They kept playing in the indoor cafe, this time with a calmer and kinder plan."
        ))
    if f.get("tension"):
        qa.append((
            "What changed after the mistaken glance?",
            f"{a.id} felt hurt at first, but the truth brought the feeling down. Once the statue was confirmed safe and {b.id} apologized, the hurt could soften into warmth."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["artifact"].tags) | set(world.facts["look"].tags)
    if world.facts.get("reconciled"):
        tags.add("apology")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="cafe", artifact="statue", look="glance", response="check",
                child_a="Mina", child_b="Ravi", parent="grownup", trait="careful", delay=0),
    StoryParams(setting="corner", artifact="statue", look="glance", response="hug",
                child_a="Lena", child_b="Kai", parent="grownup", trait="kind", delay=0),
    StoryParams(setting="cafe", artifact="rocket", look="peek", response="check",
                child_a="Tia", child_b="Owen", parent="grownup", trait="thoughtful", delay=0),
]


def explain_rejection(artifact: Artifact, look: Look) -> str:
    if not glance_risk(look, artifact):
        return f"(No story: a {look.label} is too gentle for this little conflict with the {artifact.label}.)"
    return "(No story: this combination does not support the intended story shape.)"


ASP_RULES = r"""
hazard(L, A) :- sharp(L), chipable(A).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S, L, A) :- setting(S), look(L), artifact(A), hazard(L, A).

tension :- hurt(a).
reconciled :- apology(b).
outcome(reconciled) :- reconciled.
outcome(tense) :- tension, not reconciled.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        if a.can_chip:
            lines.append(asp.fact("chipable", aid))
    for lid, l in LOOKS.items():
        lines.append(asp.fact("look", lid))
        if l.kind == "sharp":
            lines.append(asp.fact("sharp", lid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("hurt", "a"), asp.fact("apology", "b")])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced story text.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generate() smoke test failed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-cafe reconciliation storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--look", choices=LOOKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-a")
    ap.add_argument("--child-b")
    ap.add_argument("--parent")
    ap.add_argument("--trait", choices=sorted(SPACE_TRAITS))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.artifact and args.look:
        if not glance_risk(LOOKS[args.look], ARTIFACTS[args.artifact]):
            raise StoryError(explain_rejection(ARTIFACTS[args.artifact], LOOKS[args.look]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.look is None or c[1] == args.look)
              and (args.artifact is None or c[2] == args.artifact)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, look, artifact = rng.choice(sorted(combos))
    child_a = args.child_a or rng.choice(["Mina", "Lena", "Tia", "Noor"])
    child_b = args.child_b or rng.choice([n for n in ["Ravi", "Owen", "Milo", "Kai"] if n != child_a])
    parent = args.parent or "grown-up"
    trait = args.trait or rng.choice(sorted(SPACE_TRAITS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    return StoryParams(setting=setting, artifact=artifact, look=look, response=response,
                       child_a=child_a, child_b=child_b, parent=parent, trait=trait, delay=delay)


def generate(params: StoryParams) -> StorySample:
    for key, table in [("setting", SETTINGS), ("artifact", ARTIFACTS), ("look", LOOKS), ("response", RESPONSES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"invalid {key}: {getattr(params, key)}")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(f"response {params.response} is too weak for this world")
    world = tell(SETTINGS[params.setting], ARTIFACTS[params.artifact], LOOKS[params.look],
                 RESPONSES[params.response], child_a=params.child_a, child_b=params.child_b,
                 parent=params.parent, delay=params.delay)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(f"sensible responses: {', '.join(r.id for r in sensible_responses())}\n")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
