#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/consent_stove_rhyme_adventure.py
=================================================================

A standalone story world for a tiny adventure about **consent** and a **stove**:
two children are on a pretend quest, one wants to cook a snack, the other must
agree before helping, and a careful adult teaches safe stove rules with a rhymed,
child-facing ending.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes,
- state-driven causality,
- a reasonableness gate,
- inline ASP twin facts/rules,
- three Q&A sets grounded in simulated state.

This world supports the shared Storyweavers CLI contract:
    --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    place: str
    adventure: str
    dark_spot: str
    ending_image: str


@dataclass
class ConsentObject:
    id: str
    label: str
    phrase: str
    reason: str
    tag: str


@dataclass
class StoveItem:
    id: str
    label: str
    phrase: str
    danger: str
    heat: str
    flammable: bool = False


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tag: str


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_heat(world: World) -> list[str]:
    out: list[str] = []
    stove = world.get("stove")
    if stove.meters["hot"] < THRESHOLD:
        return out
    sig = ("heat", "stove")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.characters():
        e.memes["care"] += 1
    out.append("__heat__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    if world.get("pan").meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill", "pan")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("stove").meters["mess"] += 1
    for e in world.characters():
        e.memes["worry"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [
    Rule("heat", "physical", _r_heat),
    Rule("spill", "physical", _r_spill),
]


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


def hazard_at_risk(consent_obj: ConsentObject, stove_item: StoveItem) -> bool:
    return consent_obj.tag == "ask_permission" and stove_item.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= fire_severity(delay)


def _do_heat(world: World, narrate: bool = True) -> None:
    world.get("stove").meters["hot"] += 1
    propagate(world, narrate=narrate)


def predict_spill(world: World) -> dict:
    sim = world.copy()
    _do_spill(sim, narrate=False)
    return {
        "spilled": sim.get("pan").meters["spilled"] >= THRESHOLD,
        "mess": sim.get("stove").meters["mess"],
    }


def _do_spill(world: World, narrate: bool = True) -> None:
    world.get("pan").meters["spilled"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, adventurers: tuple[Entity, Entity], scene: Scene) -> None:
    a, b = adventurers
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright little afternoon, {a.id} and {b.id} set out on an adventure in {scene.place}. "
        f"{scene.adventure}"
    )
    world.say(
        f"They loved the path ahead, and the camp-stove looked like a tiny ship with a shiny flame."
    )


def desire(world: World, hero: Entity, helper: Entity, consent_obj: ConsentObject) -> None:
    hero.memes["want"] += 1
    world.say(
        f'{hero.id} pointed at the stove and said, "May I help?" {helper.id} paused, '
        f"because real help begins with {consent_obj.label}."
    )


def ask_consent(world: World, helper: Entity, hero: Entity, consent_obj: ConsentObject) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} smiled and said, "We ask first. That is our rule of the road." '
        f'"We need {consent_obj.phrase} before we touch the stove."'
    )


def refuse_or_agree(world: World, hero: Entity, helper: Entity, consent_obj: ConsentObject) -> bool:
    hero.memes["patience"] += 1
    world.say(
        f'{hero.id} thought about it, then nodded. "I can wait," {hero.id} said. '
        f'"Consent means the answer is yes before hands go near."'
    )
    return True


def stumble(world: World) -> None:
    world.say(
        "But the adventure got bumpy, and a pan tipped with a soft clink."
    )
    _do_spill(world, narrate=False)


def alarm(world: World, helper: Entity) -> None:
    helper.memes["worry"] += 1
    world.say(
        f'{helper.id} gasped, "The pan spilled!" and reached for the grown-up right away.'
    )


def rescue(world: World, adult: Entity, response: Response) -> None:
    body = response.text
    world.say(
        f"{adult.label_word.capitalize()} came to help and {body}."
    )
    world.say(
        "The stove stopped hissing, the little mess was cleared, and the bright danger settled down."
    )


def lesson(world: World, adult: Entity, hero: Entity, helper: Entity, consent_obj: ConsentObject) -> None:
    for e in (hero, helper):
        e.memes["relief"] += 1
        e.memes["lesson"] += 1
    world.say("For a moment, everyone was quiet.")
    world.say(
        f"Then {adult.label_word.capitalize()} knelt and said, "
        f'"Thank you for asking first. {consent_obj.reason}."'
    )
    world.say(
        f'"When we have consent, we move together like a team," {adult.label_word.capitalize()} said. '
        f'"When a stove is hot, we use careful hands and a grown-up’s watchful eyes."'
    )
    world.say(
        f'{hero.id} and {helper.id} promised to ask, listen, and wait.'
    )


def ending(world: World, scene: Scene, hero: Entity, helper: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(scene.ending_image)
    world.say(
        f"In the end, {hero.id} and {helper.id} marched on with happy feet, '
        f'knowing that consent and caution were part of the adventure.'"
    )


def _do_spill(world: World, narrate: bool = True) -> None:
    world.get("pan").meters["spilled"] += 1
    world.get("pan").meters["mess"] += 1
    propagate(world, narrate=narrate)


def tell(scene: Scene, consent_obj: ConsentObject, stove_item: StoveItem, response: Response,
         hero_name: str = "Mila", helper_name: str = "Jasper", hero_gender: str = "girl",
         helper_gender: str = "boy", adult_type: str = "mother", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the adult"))
    world.add(Entity(id="stove", type="stove", label=stove_item.label))
    world.add(Entity(id="pan", type="pan", label="the pan"))

    intro(world, (hero, helper), scene)
    world.para()
    desire(world, hero, helper, consent_obj)
    ask_consent(world, helper, hero, consent_obj)
    refuse_or_agree(world, hero, helper, consent_obj)

    world.para()
    _do_heat(world, narrate=False)
    stumble(world)
    alarm(world, helper)
    contained = is_contained(response, delay)
    world.facts["contained"] = contained
    world.facts["delay"] = delay

    world.para()
    if contained:
        rescue(world, adult, response)
        lesson(world, adult, hero, helper, consent_obj)
        world.para()
        ending(world, scene, hero, helper)
        outcome = "contained"
    else:
        world.say(
            f"{adult.label_word.capitalize()} tried {response.fail}."
        )
        world.say(
            "The hot mess kept growing, so everyone hurried outside and watched the steam fade from the door."
        )
        world.say(
            "Afterward, they remembered to call for help sooner the next time the stove got too wild."
        )
        outcome = "burned"

    world.facts.update(
        hero=hero, helper=helper, adult=adult, scene=scene,
        consent_obj=consent_obj, stove_item=stove_item, response=response,
        outcome=outcome, consent_given=True, answer_yes=True,
    )
    return world


SCENES = {
    "harbor": Scene("harbor", "the harbor kitchen", "Their quest was to make warm tea before the ship sailed.", "the stove corner", "The lanterns glowed, the tea steamed, and the map on the wall looked brave."),
    "camps": Scene("camps", "the camp kitchen", "Their quest was to cook supper before sunset touched the tents.", "the stove corner", "The soup simmered, the fire sang softly, and the trail waited outside."),
    "castle": Scene("castle", "the castle kitchen", "Their quest was to bake bread before the knight's parade began.", "the stove nook", "The bread smelled sweet, the banners lifted, and the castle seemed ready for a feast."),
}

CONSENT_OBJECTS = {
    "ask_permission": ConsentObject("ask_permission", "consent", "consent", "Consent means everyone agrees before we begin.", "ask_permission"),
    "permission": ConsentObject("permission", "permission", "permission", "Permission keeps hands and plans in the same direction.", "ask_permission"),
}

STOVES = {
    "stove": StoveItem("stove", "stove", "the stove", "hot and sharp", "warm"),
}

RESPONSES = {
    "wait": Response("wait", 3, 3, "turned off the burner and waited beside the stove until the heat calmed down", "waited too long and the pan kept steaming", "turned off the burner and waited until the heat calmed down", "wait"),
    "cover": Response("cover", 3, 2, "covered the pan carefully and moved it to a cool spot", "covered the pan, but the spill was already too lively", "covered the pan carefully and moved it to a cool spot", "cover"),
    "towel": Response("towel", 2, 2, "used a folded towel to guide the pan to safety", "used a towel, but the spill was too big to tame", "used a folded towel to guide the pan to safety", "towel"),
    "water_bucket": Response("water_bucket", 1, 1, "threw a little water on it", "threw a little water on it, but it did not help much", "threw a little water on it", "water"),
}

GIRL_NAMES = ["Mila", "Nia", "Luna", "Ivy", "Zoe", "Ari", "Tess", "Eli", "Ada", "Rae"]
BOY_NAMES = ["Jasper", "Noah", "Theo", "Finn", "Leo", "Evan", "Owen", "Milo", "Ben", "Kai"]

CURATED = [
    StoryParams("harbor", "ask_permission", "stove", "wait", "Mila", "Jasper", "girl", "boy", "mother", 0),
    StoryParams("camps", "permission", "stove", "cover", "Theo", "Luna", "boy", "girl", "father", 0),
    StoryParams("castle", "ask_permission", "stove", "towel", "Ari", "Finn", "girl", "boy", "mother", 1),
]


@dataclass
class StoryParams:
    scene: str
    consent: str
    stove: str
    response: str
    hero: str
    helper: str
    hero_gender: str
    helper_gender: str
    adult: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for c in CONSENT_OBJECTS:
            for st in STOVES:
                if hazard_at_risk(CONSENT_OBJECTS[c], STOVES[st]):
                    combos.append((s, c, st))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the word "consent" and the word "stove".',
        f"Tell a rhyme-filled adventure where {f['hero'].id} and {f['helper'].id} must ask for consent before helping at the stove.",
        f"Write a small quest story where a stove makes trouble, a grown-up helps, and the children learn to ask first.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, adult = f["hero"], f["helper"], f["adult"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, {helper.id}, and {adult.label_word}. They are the small adventurers who learn a careful rule on their quest."),
        ("What did they need before helping?",
         f"They needed consent before helping at the stove. That meant everyone agreed first, so no one was surprised when the hands moved in."),
        ("Why did the adult step in?",
         f"The pan spilled and the stove got messy, so the adult stepped in to help. The quick help kept the trouble from turning into a bigger problem."),
    ]
    if f.get("outcome") == "contained":
        qa.append((
            "How did the story end?",
            f"It ended safely, with the spill handled and the stove calmed down. The children learned that consent and care belong in every adventure."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is consent?",
         "Consent is when someone agrees to something before it happens. It helps people work together kindly and safely."),
        ("What is a stove?",
         "A stove is a kitchen tool that gets hot so people can cook food. Because it gets hot, children should be careful around it."),
        ("Why should you ask before helping with something hot?",
         "You should ask first so everyone knows the plan and can stay safe. Hot things can hurt hands, so adults need to guide the job."),
        ("Why is it good to work together on an adventure?",
         "Working together helps everyone stay brave, calm, and ready. A team can solve problems better than one child alone."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(C, S) :- consent_obj(C), stove_item(S), consent_tag(C), flammable(S).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
valid(Scene, Consent, Stove) :- scene(Scene), consent_obj(Consent), stove_item(Stove), hazard(Consent, Stove).

heat(stove) :- stove_hot.
spilled(pan) :- pan_spilled.
outcome(contained) :- spill, sensible(_).
outcome(burned) :- spill, not sensible(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid in CONSENT_OBJECTS:
        lines.append(asp.fact("consent_obj", cid))
        lines.append(asp.fact("consent_tag", cid))
    for sid in STOVES:
        lines.append(asp.fact("stove_item", sid))
        lines.append(asp.fact("flammable", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify passed and generation smoke test succeeded.")
    return rc


def explain_rejection(consent_obj: ConsentObject, stove_item: StoveItem) -> str:
    if not hazard_at_risk(consent_obj, stove_item):
        return "(No story: the chosen objects do not make a useful consent-and-stove adventure.)"
    return "(No story: this combination is invalid for the tiny adventure world.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny adventure world about consent and a stove.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--consent", choices=CONSENT_OBJECTS)
    ap.add_argument("--stove", choices=STOVES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.consent is None or c[1] == args.consent)
              and (args.stove is None or c[2] == args.stove)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, consent, stove = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero = args.hero or rng.choice(GIRL_NAMES)
    helper = args.helper or rng.choice([n for n in BOY_NAMES if n != hero])
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(scene, consent, stove, response, hero, helper, "girl" if hero in GIRL_NAMES else "boy", "boy" if helper in BOY_NAMES else "girl", adult)


def tell_scene(params: StoryParams) -> World:
    scene = SCENES[params.scene]
    consent_obj = CONSENT_OBJECTS[params.consent]
    stove_item = STOVES[params.stove]
    response = RESPONSES[params.response]
    return tell(scene, consent_obj, stove_item, response, params.hero, params.helper,
                params.hero_gender, params.helper_gender, params.adult, params.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell_scene(params)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for t in asp_valid_combos():
            print(t)
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
            header = f"### {p.hero} & {p.helper}: {p.scene} / {p.response}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
