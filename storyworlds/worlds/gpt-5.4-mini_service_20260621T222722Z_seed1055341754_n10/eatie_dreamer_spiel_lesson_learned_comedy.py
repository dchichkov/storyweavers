#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260621T222722Z_seed1055341754_n10/eatie_dreamer_spiel_lesson_learned_comedy.py
===============================================================================================================

A standalone storyworld for a tiny comedic domain about a kid called Eatie,
a dreamy classmate, and a noisy "spiel" that keeps getting rehearsed at the
wrong times. The lesson learned is simple: telling the truth plainly works
better than a big dramatic speech.

The world is built around a small school-day comedy:
- Eatie wants a snack before the class presentation.
- Dreamer rehearses a big spiel instead of noticing what is happening.
- A small mishap turns into a comic scramble.
- A grown-up or peer helps them slow down, speak clearly, and fix it.
- The ending proves the lesson learned: less grandstanding, more honesty.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports shared results eagerly
- imports shared ASP lazily inside helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

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
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    place_text: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    crumbs: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Speech:
    id: str
    label: str
    style: str
    volume: int
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpMove:
    id: str
    label: str
    method: str
    sense: int
    relief: int
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


def _r_giggle(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["sticky"] < THRESHOLD:
            continue
        sig = ("giggle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for who in world.entities.values():
            if who.kind == "character":
                who.memes["amusement"] += 1
        out.append("__giggle__")
    return out


def _r_rumple(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["crumbly"] < THRESHOLD:
            continue
        sig = ("rumple", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("room").meters["mess"] += 1
        out.append("__mess__")
    return out


CAUSAL_RULES = [Rule("giggle", _r_giggle), Rule("rumple", _r_rumple)]


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


def reasonableness_ok(snack: Snack, speech: Speech, helpmove: HelpMove) -> bool:
    return speech.sense >= SENSE_MIN and helpmove.sense >= SENSE_MIN and snack.id in SNACKS and speech.id in SPEECHES and helpmove.id in HELPMOVES


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for snack in SNACKS:
            for speech in SPEECHES:
                for move in HELPMOVES:
                    if reasonableness_ok(SNACKS[snack], SPEECHES[speech], HELPMOVES[move]):
                        combos.append((sid, snack, speech, move))
    return combos


def snack_risk(snack: Snack) -> bool:
    return True


def help_fits(helpmove: HelpMove, snack: Snack) -> bool:
    return helpmove.relief >= 1 and snack_risk(snack)


def lecture_too_long(speech: Speech) -> bool:
    return speech.volume >= 7


def predict_mess(world: World, snack_id: str) -> dict:
    sim = world.copy()
    sim.get(snack_id).meters["crumbly"] += 1
    propagate(sim, narrate=False)
    return {"mess": sim.get("room").meters["mess"], "sticky": sim.get(snack_id).meters["sticky"]}


def eat_snack(world: World, eater: Entity, snack: Snack) -> None:
    eater.memes["hunger"] += 1
    eater.meters["sticky"] += 1
    world.get("snack").meters["crumbly"] += 1
    world.say(f"{eater.id} took one bite of the {snack.label}, and crumbs began to tumble like tiny snowflakes.")
    propagate(world)


def spill(speaker: Entity, speech: Speech) -> None:
    speaker.memes["nervous"] += 1


def monologue(world: World, dreamer: Entity, speech: Speech, snack: Snack) -> None:
    world.say(
        f'{dreamer.id} launched into a {speech.style} spiel about "{speech.label}", '
        f"waving {dreamer.pronoun('possessive')} hands like a tiny stage star."
    )
    if lecture_too_long(speech):
        world.say(
            f"The spiel went on so long that nobody noticed the {snack.label} getting crumbly on the desk."
        )
    else:
        world.say(
            f"The spiel was short enough to fit between two blinks, which almost helped."
        )


def warning(world: World, helper: Entity, dreamer: Entity, snack: Snack, speech: Speech) -> None:
    pred = predict_mess(world, "snack")
    helper.memes["concern"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{helper.id} frowned. "If {dreamer.id} keeps talking and {dreamer.pronoun()} '
        f"keeps munching, the desk will get messy, and then the whole room will feel like a picnic gone wrong."'
    )


def reset_focus(world: World, helper: Entity, dreamer: Entity, snack: Snack, move: HelpMove) -> None:
    dreamer.memes["nervous"] = 0
    dreamer.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} showed {dreamer.id} how to wipe the crumbs first and then speak plainly."
    )
    world.say(
        f'They used {move.label}, and the silly wobble in the room settled down at once.'
    )


def lesson_learned(world: World, dreamer: Entity, helper: Entity, snack: Snack) -> None:
    dreamer.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say("For a moment, both of them just smiled at the quiet desk.")
    world.say(
        f'{dreamer.id} grinned. "Next time, I will skip the giant spiel and just say what I mean," '
        f'{dreamer.id} said.'
    )
    world.say(
        f'{helper.id} nodded. "And maybe keep the {snack.label} away from the notes," '
        f'{helper.pronoun()} added.'
    )


def wrap_up(world: World, dreamer: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"By the end of class, the paper was neat again, the snack was finished, and "
        f"{dreamer.id} was telling the truth in plain words instead of a parade of speeches."
    )
    world.say(
        f"Even the {setting.label} seemed to laugh along, bright as a stage light after the joke landed."
    )


def tell(setting: Setting, snack: Snack, speech: Speech, helpmove: HelpMove,
         dreamer_name: str = "Dreamer", dreamer_type: str = "boy",
         helper_name: str = "Teacher", helper_type: str = "teacher",
         eatie_name: str = "Eatie") -> World:
    world = World()
    dreamer = world.add(Entity(id=dreamer_name, kind="character", type=dreamer_type, role="dreamer"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    eatie = world.add(Entity(id=eatie_name, kind="character", type="boy", role="eatie"))
    room = world.add(Entity(id="room", type="room", label=setting.label))
    snack_ent = world.add(Entity(id="snack", type="snack", label=snack.label))
    world.facts.update(setting=setting, snack_cfg=snack, speech_cfg=speech, helpmove_cfg=helpmove)
    world.say(f"At {setting.place_text}, {eatie.id}, {dreamer.id}, and {helper.id} were trying to keep a very funny day on track.")
    world.say(f"{eatie.id} was hungry for a bite of {snack.label}, and {dreamer.id} was already practicing a big spiel for the class show.")
    world.para()
    eat_snack(world, eatie, snack)
    monologue(world, dreamer, speech, snack)
    warning(world, helper, dreamer, snack, speech)
    world.para()
    if help_fits(helpmove, snack):
        reset_focus(world, helper, dreamer, snack, helpmove)
        lesson_learned(world, dreamer, helper, snack)
    else:
        world.say("The attempt to fix it was too small to matter, so the laughter kept getting louder.")
    wrap_up(world, dreamer, helper, setting)
    world.facts.update(
        dreamer=dreamer,
        helper=helper,
        eatie=eatie,
        room=room,
        snack=snack_ent,
        outcome="cleaned",
    )
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        label="the classroom",
        place_text="the classroom after lunch",
        mood="bright",
        tags={"school", "room"},
    ),
    "auditorium": Setting(
        id="auditorium",
        label="the auditorium",
        place_text="the auditorium stage",
        mood="echoey",
        tags={"school", "stage"},
    ),
}

SNACKS = {
    "cookie": Snack(id="cookie", label="cookie", phrase="a crumbly cookie", crumbs="crumbs", tags={"food"}),
    "muffin": Snack(id="muffin", label="muffin", phrase="a soft muffin", crumbs="crumbs", tags={"food"}),
    "pretzel": Snack(id="pretzel", label="pretzel", phrase="a twisty pretzel", crumbs="crumbs", tags={"food"}),
}

SPEECHES = {
    "spiel": Speech(id="spiel", label="the spiel", style="grand", volume=8, sense=3, tags={"speech", "comedy"}),
    "mini_spiel": Speech(id="mini_spiel", label="the mini spiel", style="cheerful", volume=4, sense=3, tags={"speech", "comedy"}),
    "whisper": Speech(id="whisper", label="a whisper", style="tiny", volume=1, sense=2, tags={"speech"}),
}

HELPMOVES = {
    "wipe_and_pause": HelpMove(id="wipe_and_pause", label="a quick wipe-and-pause", method="wipe", sense=3, relief=2, tags={"help"}),
    "take_a_breath": HelpMove(id="take_a_breath", label="a deep breath and a tissue", method="breathe", sense=3, relief=2, tags={"help"}),
    "slow_down": HelpMove(id="slow_down", label="a slow-down sign", method="slow", sense=2, relief=1, tags={"help"}),
}

TRAITS = ["curious", "earnest", "goofy", "careful", "chatty"]
EATIE_NAMES = ["Eatie", "Nina", "Milo", "Pip", "Rae"]


@dataclass
class StoryParams:
    setting: str
    snack: str
    speech: str
    helpmove: str
    dreamer_name: str = "Dreamer"
    dreamer_type: str = "boy"
    helper_name: str = "Teacher"
    helper_type: str = "teacher"
    eatie_name: str = "Eatie"
    trait: str = "goofy"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: eatie, dreamer, spiel, and a lesson learned comedy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--speech", choices=SPEECHES)
    ap.add_argument("--helpmove", choices=HELPMOVES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.snack is None or c[1] == args.snack)
              and (args.speech is None or c[2] == args.speech)
              and (args.helpmove is None or c[3] == args.helpmove)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, snack, speech, helpmove = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        snack=snack,
        speech=speech,
        helpmove=helpmove,
        dreamer_name=rng.choice(["Dreamer", "Noah", "Luna"]),
        dreamer_type=rng.choice(["boy", "girl"]),
        helper_name=rng.choice(["Teacher", "Mimi", "Coach"]),
        helper_type=rng.choice(["teacher", "mother", "father"]),
        eatie_name=rng.choice(EATIE_NAMES),
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.snack not in SNACKS or params.speech not in SPEECHES or params.helpmove not in HELPMOVES:
        raise StoryError("Invalid StoryParams values.")
    world = tell(SETTINGS[params.setting], SNACKS[params.snack], SPEECHES[params.speech], HELPMOVES[params.helpmove],
                 dreamer_name=params.dreamer_name, dreamer_type=params.dreamer_type,
                 helper_name=params.helper_name, helper_type=params.helper_type,
                 eatie_name=params.eatie_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a small child that includes the words "{f["eatie"].id}", "{f["dreamer"].id}", and "{f["speech_cfg"].label}".',
        f"Tell a classroom comedy where {f['eatie'].id} wants a snack while {f['dreamer'].id} keeps making a {f['speech_cfg'].label} and learns a lesson.",
        f"Write a short lesson-learned story with a silly {f['speech_cfg'].style} speech, a crumbly snack, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    eatie = f["eatie"]
    dreamer = f["dreamer"]
    helper = f["helper"]
    snack = f["snack_cfg"]
    speech = f["speech_cfg"]
    helpmove = f["helpmove_cfg"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who are the main characters in the {setting.label} story?",
            answer=f"The story follows {eatie.id}, {dreamer.id}, and {helper.id}. {eatie.id} brings the snack trouble, {dreamer.id} brings the spiel trouble, and {helper.id} brings the lesson learned.",
        ),
        QAItem(
            question=f"Why did {dreamer.id} get in trouble during the spiel?",
            answer=f"{dreamer.id} kept making a big {speech.label} while the {snack.label} got crumbly on the desk. The noisy speech made the moment silly enough that nobody noticed the mess right away.",
        ),
        QAItem(
            question=f"What did {helper.id} do to help fix the problem?",
            answer=f"{helper.id} used {helpmove.label} and asked everyone to slow down. That helped the room settle, and it made the lesson learned feel cheerful instead of scoldy.",
        ),
        QAItem(
            question=f"What lesson did {dreamer.id} learn by the end?",
            answer=f"{dreamer.id} learned that a plain sentence works better than a giant spiel when something needs fixing. {dreamer.id} also learned to wipe up crumbs before the next big idea.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["snack_cfg"].tags) | set(f["speech_cfg"].tags) | set(f["helpmove_cfg"].tags)
    out: list[QAItem] = []
    if "food" in tags:
        out.append(QAItem("What is a crumb?", "A crumb is a tiny piece of food that falls off something like a cookie or muffin. Crumbs can make a desk messy if they pile up."))
    if "speech" in tags:
        out.append(QAItem("What is a spiel?", "A spiel is a long excited speech. It can be funny, but it can also go on too long if nobody stops to listen."))
    if "help" in tags:
        out.append(QAItem("What does it mean to slow down?", "Slowing down means taking a breath and doing one thing at a time. It helps people notice what is happening and fix problems more calmly."))
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="classroom", snack="cookie", speech="spiel", helpmove="wipe_and_pause", dreamer_name="Dreamer", dreamer_type="boy", helper_name="Teacher", helper_type="teacher", eatie_name="Eatie", trait="goofy"),
    StoryParams(setting="auditorium", snack="muffin", speech="mini_spiel", helpmove="take_a_breath", dreamer_name="Luna", dreamer_type="girl", helper_name="Mimi", helper_type="mother", eatie_name="Eatie", trait="curious"),
]


def explain_rejection() -> str:
    return "(No story: this combination is too flat or not comedic enough for the lesson-learned setup.)"


ASP_RULES = r"""
valid(S, N, P, H) :- setting(S), snack(N), speech(P), helpmove(H).
sensible(P) :- speech(P), sense(P, X), sense_min(M), X >= M.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid, n in SNACKS.items():
        lines.append(asp.fact("snack", nid))
    for pid, p in SPEECHES.items():
        lines.append(asp.fact("speech", pid))
        lines.append(asp.fact("sense", pid, p.sense))
    for hid in HELPMOVES:
        lines.append(asp.fact("helpmove", hid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    else:
        print("OK: ASP and Python combo gates match.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, n, p, h) for s in SETTINGS for n in SNACKS for p in SPEECHES if SPEECHES[p].sense >= SENSE_MIN for h in HELPMOVES if HELPMOVES[h].sense >= SENSE_MIN]


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    return generation_prompts(world)


def story_qa(world: World) -> list[QAItem]:
    return story_qa(world)


def world_knowledge_qa(world: World) -> list[QAItem]:
    return world_knowledge_qa(world)


if __name__ == "__main__":
    main()
