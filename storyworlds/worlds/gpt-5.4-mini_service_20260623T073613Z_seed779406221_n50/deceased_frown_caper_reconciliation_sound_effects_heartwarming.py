#!/usr/bin/env python3
"""
storyworlds/worlds/deceased_frown_caper_reconciliation_sound_effects_heartwarming.py
====================================================================================

A standalone storyworld for a heartwarming small-domain tale about a childish
caper, a worried frown, and a gentle reconciliation after the memory of someone
deceased is accidentally stirred up by loud sound effects.

Premise:
- A child plans a playful caper with sound effects.
- An adult frowns because the sounds echo in a room holding a keepsake from a
  deceased loved one.
- The caper turns tender when the child notices the hurt, apologizes, and
  helps create a softer tribute.
- The ending proves the change through a warm shared moment.

This world uses:
- typed entities with physical meters and emotional memes
- a causal state model that drives prose
- a Python reasonableness gate
- an inline ASP twin for parity verification
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    owner: str = ""
    caretaker: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noise": 0.0, "tidy": 0.0, "warmth": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "frown": 0.0, "grief": 0.0, "reconciliation": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    quiet: bool
    keepsake_spot: str


@dataclass
class Caper:
    id: str
    setup: str
    sound: str
    verb: str
    mess: str
    emotion: str


@dataclass
class Tribute:
    id: str
    label: str
    phrase: str
    sound: str


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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_noise(world: World) -> list[str]:
    out = []
    child = world.get("child")
    adult = world.get("adult")
    if child.meters["noise"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    adult.memes["frown"] += 1
    if "keepsake" in world.entities:
        world.get("keepsake").meters["shake"] += 1
    out.append("__noise__")
    return out


def _r_frown_to_grief(world: World) -> list[str]:
    out = []
    adult = world.get("adult")
    if adult.memes["frown"] < THRESHOLD:
        return out
    sig = ("grief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    adult.memes["grief"] += 1
    out.append("The room felt a little heavier.")
    return out


def _r_reconcile(world: World) -> list[str]:
    child = world.get("child")
    adult = world.get("adult")
    if child.memes["apology"] < THRESHOLD or adult.memes["grief"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["reconciliation"] += 1
    adult.memes["reconciliation"] += 1
    child.meters["noise"] = 0.0
    adult.memes["frown"] = 0.0
    return ["__reconcile__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_noise, _r_frown_to_grief, _r_reconcile):
            res = fn(world)
            if res:
                changed = True
                out.extend(x for x in res if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(setting: Setting, caper: Caper, tribute: Tribute) -> bool:
    return bool(setting.quiet and caper.sound and tribute.sound)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, t) for s in SETTINGS for c in CAPERS for t in TRIBUTES if reasonableness_gate(SETTINGS[s], CAPERS[c], TRIBUTES[t])]


def predict_reconcile(world: World, child: Entity) -> bool:
    sim = world.copy()
    sim.get("child").meters["noise"] += 1
    propagate(sim, narrate=False)
    return sim.get("adult").memes["grief"] >= THRESHOLD


def tell(setting: Setting, caper: Caper, tribute: Tribute, child_name: str, adult_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="boy", label=child_name))
    adult = world.add(Entity(id="adult", kind="character", type="aunt", label=adult_name))
    deceased = world.add(Entity(id="deceased", kind="memory", type="woman", label="Grandma Rose"))
    keepsake = world.add(Entity(id="keepsake", type="thing", label="music box", phrase="a small music box"))
    child.meters["noise"] = 0.0
    adult.memes["grief"] = 0.0
    deceased.memes["warmth"] = 1.0
    keepsake.caretaker = "adult"

    world.say(f"{child.label} loved little capers, especially the ones with sound effects.")
    world.say(f"{adult.label} kept {deceased.label}'s {keepsake.label} on a shelf by {setting.keepsake_spot}.")
    world.say(f"One day {child.label} planned a caper: {caper.setup} {caper.sound}.")
    world.para()
    world.say(f"{child.label} began the caper, and {caper.sound} went the room.")
    child.meters["noise"] += 1
    propagate(world)
    world.say(f"{adult.label} gave a frown and held {adult.pronoun('possessive')} breath for a moment.")

    world.para()
    if adult.memes["grief"] >= THRESHOLD:
        world.say(f"{child.label} saw that frown and stopped the caper at once.")
        child.memes["apology"] = 1.0
        world.say(f'"I am sorry," {child.label} said softly. "I did not mean to make you sad."')
        child.meters["noise"] = 0.0
        child.meters["tidy"] += 1
        world.say(f"{child.label} set the {keepsake.label} back carefully and tried a gentler sound: {tribute.sound}.")
        child.meters["noise"] += 0.5
        adult.memes["grief"] += 0.0
        propagate(world)
        if adult.memes["reconciliation"] >= THRESHOLD or child.memes["reconciliation"] >= THRESHOLD:
            world.say(f"{adult.label} smiled through the tears and hugged {child.label}.")
            world.say(f'Together they listened to {tribute.sound} and remembered {deceased.label} with warm hearts.')
            world.say(f"The little room felt soft again, and the {keepsake.label} stayed safe and still.")
            adult.meters["warmth"] += 1
    else:
        world.say(f"{adult.label} only blinked, and the room stayed calm.")
        world.say(f"{child.label} finished the caper and then shared {tribute.sound} as a surprise tribute.")

    world.facts.update(
        child=child,
        adult=adult,
        deceased=deceased,
        keepsake=keepsake,
        setting=setting,
        caper=caper,
        tribute=tribute,
    )
    return world


SETTINGS = {
    "quiet_room": Setting(place="the quiet room", quiet=True, keepsake_spot="the window"),
    "porch": Setting(place="the porch", quiet=True, keepsake_spot="the little table"),
    "kitchen": Setting(place="the kitchen", quiet=True, keepsake_spot="the shelf"),
}

CAPERS = {
    "drums": Caper(id="drums", setup="a tiny drum parade", sound="bam-bam-bam", verb="drum", mess="rattle", emotion="play"),
    "shoes": Caper(id="shoes", setup="a shoe-tiptoe caper", sound="tip-tap, tip-tap", verb="tiptoe", mess="tap", emotion="mischief"),
    "bells": Caper(id="bells", setup="a bell-ring caper", sound="ding-ding!", verb="ring", mess="jingle", emotion="glee"),
}

TRIBUTES = {
    "humming": Tribute(id="humming", label="humming", phrase="a soft hum", sound="mmm-hmm"),
    "clapping": Tribute(id="clapping", label="clapping", phrase="gentle claps", sound="clap... clap..."),
    "whistling": Tribute(id="whistling", label="whistling", phrase="a tiny whistle", sound="fwee-fwee"),
}

GIRL_NAMES = ["Mia", "Lina", "June", "Ava", "Nora"]
BOY_NAMES = ["Leo", "Finn", "Owen", "Max", "Eli"]


@dataclass
class StoryParams:
    setting: str
    caper: str
    tribute: str
    child: str
    adult: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about a child named {f["child"].label} who plans a small caper with sound effects in {f["setting"].place}.',
        f"Tell a gentle story where {f['adult'].label} frowns at {f['caper'].sound}, and {f['child'].label} makes things right with a soft tribute.",
        f'Write a reconciliation story that includes the words "deceased", "frown", and "{f["tribute"].sound}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, deceased, caper, tribute = f["child"], f["adult"], f["deceased"], f["caper"], f["tribute"]
    return [
        QAItem(
            question=f"What kind of caper did {child.label} plan?",
            answer=f"{child.label} planned {caper.setup}, and the whole idea used {caper.sound} as its sound effect."
        ),
        QAItem(
            question=f"Why did {adult.label} frown during the caper?",
            answer=f"{adult.label} frowned because the noisy {caper.sound} made the room feel too loud near {deceased.label}'s keepsake. That sound stirred up sadness, so {child.label} noticed and slowed down."
        ),
        QAItem(
            question=f"How did {child.label} and {adult.label} reconcile?",
            answer=f"{child.label} apologized, chose gentler sounds, and shared {tribute.sound}. After that, {adult.label} hugged {child.label} and the sad feeling softened."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does a frown mean?", "A frown is a face that shows worry, sadness, or dislike."),
        QAItem("What does deceased mean?", "Deceased means someone has died. People may feel sad and remember them with care."),
        QAItem("What are sound effects?", "Sound effects are little noises that help make a game, story, or play feel lively."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: the chosen combination does not create a quiet enough place for a meaningful frown-and-reconciliation beat.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming caper storyworld with sound effects and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--caper", choices=CAPERS)
    ap.add_argument("--tribute", choices=TRIBUTES)
    ap.add_argument("--child")
    ap.add_argument("--adult")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.caper is None or c[1] == args.caper)
              and (args.tribute is None or c[2] == args.tribute)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, caper, tribute = rng.choice(sorted(combos))
    child = args.child or rng.choice(GIRL_NAMES + BOY_NAMES)
    adult = args.adult or rng.choice(["Aunt June", "Aunt Mae", "Aunt Rose"])
    return StoryParams(setting=setting, caper=caper, tribute=tribute, child=child, adult=adult)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CAPERS[params.caper], TRIBUTES[params.tribute], params.child, params.adult)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
noise_event :- child_noise.
frown_event :- noise_event.
reconcile_event :- apology, grief, frown_event.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CAPERS.items():
        lines.append(asp.fact("caper", cid))
        lines.append(asp.fact("sound", cid, c.sound))
    for tid, t in TRIBUTES.items():
        lines.append(asp.fact("tribute", tid))
        lines.append(asp.fact("sound", tid, t.sound))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show noise_event/0.\n#show frown_event/0.\n#show reconcile_event/0."))
    return 0 if model is not None else 1


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
        print(asp_program("#show noise_event/0.\n#show frown_event/0.\n#show reconcile_event/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is present; use --verify for parity checks.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            for caper in CAPERS:
                for tribute in TRIBUTES:
                    params = StoryParams(setting=setting, caper=caper, tribute=tribute, child="Mia", adult="Aunt June")
                    samples.append(generate(params))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
