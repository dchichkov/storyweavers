#!/usr/bin/env python3
"""A small superhero storyworld about bacon, a removal mistake, a twist, and reconciliation."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    mood: str
    weather: str


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    rival: str
    twist: str = ""
    reconciliation: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    missing: str
    accusation: str
    early_action: str
    early_result: str
    twist_clue: str
    truth: str
    repair: str
    ending: str


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "rooftop": Scene("the rooftop", "windy", "bright noon light"),
    "museum": Scene("the museum hall", "echoing", "soft silver rain"),
    "harbor": Scene("the harbor", "salt-sweet", "golden evening light"),
    "park": Scene("the city park", "green and busy", "warm sunshine"),
}

HEROES = {"Nova": "girl", "Bolt": "boy", "Comet": "boy", "Ruby": "girl"}
SIDEKICKS = {"Pip": "girl", "Mica": "boy", "Tess": "girl", "Quill": "boy"}
RIVALS = {"Captain Crumb": "villain", "Mirror Moth": "villain", "Sir Snap": "villain", "Grim Glide": "villain"}

CASES = {
    "bacon_tray": Case(
        missing="the bacon tray from the hero kitchen",
        accusation="the rival was seen near the pantry and everyone smelled breakfast",
        early_action="checked the kitchen roof and followed the sticky trail",
        early_result="the trail led to a skylight, but no one had stolen the tray there",
        twist_clue="a grease mark on a cape clasp",
        truth="the bacon had been moved to keep it away from a visiting rescue bird",
        repair="returned the tray, apologized to the bird keeper, and shared a calmer breakfast",
        ending="the bacon tray rested back on its stand while the rescue bird chirped from a safe perch",
    ),
    "signal_emblem": Case(
        missing="the city beacon emblem",
        accusation="the rival was holding a shiny disc during the alarm",
        early_action="searched the tower steps and timed the flashes",
        early_result="the flashes matched the clock, but the emblem was still gone",
        twist_clue="a soot-smudged stamp shaped like a hidden wing",
        truth="the emblem had been borrowed for a practice signal and tucked into a training locker",
        repair="opened the locker together, fixed the warning lamp, and thanked the rival for helping",
        ending="the beacon shone again with its emblem back in place and the whole rooftop smiling",
    ),
    "comic_pages": Case(
        missing="the comic pages for the team poster",
        accusation="the rival had torn paper from the poster board",
        early_action="glued the edges that had curled and counted every page",
        early_result="the count was wrong, but the torn board still did not explain the missing stack",
        twist_clue="a paper clip bent into a tiny lightning shape",
        truth="the pages had slipped into a fan vent during a dramatic wind burst",
        repair="fished them out, straightened the clip, and praised the rival for pointing to the vent",
        ending="the comic pages dried in a neat row beside a poster that now looked extra heroic",
    ),
    "mask_ribbons": Case(
        missing="the mask ribbons from the costume bench",
        accusation="the rival was standing beside the bench when the ribbons vanished",
        early_action="looked under the seats and asked the crowd to step back",
        early_result="the crowd moved, but the ribbons still were not under any seat",
        twist_clue="a thread of glitter caught on a broom handle",
        truth="the ribbons had snagged on the broom and been carried to the storage closet",
        repair="returned the ribbons, swept the closet clean, and made peace with a handshake",
        ending="the costume bench was tidy again, and both heroes wore their masks with bright smiles",
    ),
    "alarm_keys": Case(
        missing="the alarm keys for the sky tram",
        accusation="the rival had been heard clinking metal in the corridor",
        early_action="checked every hook by the control room door",
        early_result="the hooks were empty, but the corridor was too noisy to trust one clue",
        twist_clue="a key ring shadow inside a lunch pail",
        truth="the keys had been dropped into a lunch pail by mistake during the lunch rush",
        repair="returned the keys, thanked the staff, and invited the rival to help lock the cabinet",
        ending="the tram alarm clicked safely into place while everyone shared a relieved grin",
    ),
    "helmet_star": Case(
        missing="the star on the hero helmet",
        accusation="the rival had brushed the display case and left a scratch",
        early_action="polished the glass and searched the floor with a flashlight",
        early_result="the shine came back, but the star was still hiding somewhere else",
        twist_clue="a tiny magnet stuck to a map pin",
        truth="the star had fallen behind a map board and been held there by the magnet",
        repair="popped it free, repaired the display, and thanked the rival for noticing the magnet",
        ending="the helmet gleamed again, its star fixed high above a peaceful display case",
    ),
}

TWISTS = ("turning_point", "hidden_help", "misread_clue", "swapped_item", "quiet_signal", "wrong_shadow")
RECONCILIATIONS = ("apology", "teamwork", "shared_laugh", "new_rule", "repaired_misunderstanding", "thank_you_note")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld about bacon, a removal mistake, and a twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--sidekick", choices=sorted(SIDEKICKS))
    ap.add_argument("--rival", choices=sorted(RIVALS))
    ap.add_argument("--twist", choices=sorted(TWISTS))
    ap.add_argument("--reconciliation", choices=sorted(RECONCILIATIONS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, h, r) for p in sorted(PLACES) for h in sorted(HEROES) for r in sorted(RIVALS)]


ASP_RULES = """
valid(Place, Hero, Rival) :- place(Place), hero(Hero), rival(Rival).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            *(asp.fact("place", p) for p in PLACES),
            *(asp.fact("hero", h) for h in HEROES),
            *(asp.fact("rival", r) for r in RIVALS),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid/3.")), "valid")))


def asp_verify() -> int:
    py, cl = set(valid_combos()), set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:", sorted(py - cl), sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c
        for c in valid_combos()
        if (not args.place or c[0] == args.place)
        and (not args.hero or c[1] == args.hero)
        and (not args.rival or c[2] == args.rival)
    ]
    if not combos:
        raise StoryError("No valid superhero story fits those options.")
    place, hero, rival = rng.choice(combos)
    sidekick = args.sidekick or rng.choice([k for k in sorted(SIDEKICKS) if k != hero])
    twist = args.twist or rng.choice(TWISTS)
    reconciliation = args.reconciliation or rng.choice(RECONCILIATIONS)
    return StoryParams(place=place, hero=hero, sidekick=sidekick, rival=rival, twist=twist, reconciliation=reconciliation)


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(x) for x in (params.seed, params.place, params.hero, params.sidekick, params.rival, params.twist, params.reconciliation))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    case = CASES["bacon_tray" if params.hero in {"Nova", "Bolt"} else "comic_pages"]
    rng = story_rng(params)
    world = World(scene)

    hero = world.add(Entity(id=params.hero, kind="character", type=HEROES[params.hero], label=params.hero))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type=SIDEKICKS[params.sidekick], label=params.sidekick))
    rival = world.add(Entity(id=params.rival, kind="character", type=RIVALS[params.rival], label=params.rival))

    opening = {
        "bacon_tray": f"At {scene.place}, {hero.id} found that {case.missing} was gone. The smell of bacon drifted through the warm air, and the team rushed to help.",
        "signal_emblem": f"At {scene.place}, a siren chirped once and {case.missing} was missing. {hero.id} and {sidekick.id} raced to the tower steps.",
        "comic_pages": f"At {scene.place}, {case.missing} was missing from the display board. {hero.id} noticed the room felt strangely windy.",
        "mask_ribbons": f"At {scene.place}, {case.missing} had vanished from the costume bench. {hero.id} and {sidekick.id} searched before the next parade.",
        "alarm_keys": f"At {scene.place}, {case.missing} could not be found. {hero.id} listened for clues in the noisy corridor.",
        "helmet_star": f"At {scene.place}, {case.missing} had slipped away from the hero helmet. {hero.id} and {sidekick.id} searched the display room.",
    }
    world.say(opening["bacon_tray" if params.hero in {"Nova", "Bolt"} else "comic_pages"])
    world.say(rng.choice([
        f'"We need to remove panic, not just the missing thing," {sidekick.id} said.',
        f'"Let us be careful," {hero.id} said. "{case.missing.capitalize()} will not solve itself."',
        f'"I will help," {sidekick.id} said, standing beside {hero.id} like a bright shield.',
        f'"We can check every clue," {hero.id} said, and {sidekick.id} nodded right away.',
    ]))
    world.para()
    world.say(rng.choice([
        f"People blamed {rival.id} because {case.accusation}.",
        f'"It had to be {rival.id}," someone said, because {case.accusation}.',
        f"The crowd grew tense, since {case.accusation} made {rival.id} look suspicious.",
        f"That guess turned the search into a quarrel, because {case.accusation}.",
    ]))
    world.say(f"But {hero.id} did not want an unfair fight, so the hero slowed everyone down.")
    hero.memes["fairness"] = 1
    rival.memes["blamed"] = 1
    world.say(rng.choice([
        f'"Being nearby is not the same as being guilty," {hero.id} said.',
        f'"We need facts before blame," {sidekick.id} said, blocking the door with an open hand.',
        f'"No one gets pushed aside while we check," {hero.id} said to the crowd.',
        f'"A real hero looks twice," {hero.id} said, and the room got quieter.',
    ]))
    world.para()
    world.say(f"First, {hero.id} {case.early_action}.")
    world.say(f"But {case.early_result}.")
    world.say(rng.choice([
        f'Then came the twist: {case.twist_clue}.',
        f"The story changed when they noticed {case.twist_clue}.",
        f"{params.twist.replace('_', ' ').title()} happened when {case.twist_clue}.",
        f"A small detail flipped the case: {case.twist_clue}.",
    ]))
    world.say(f"That clue showed the truth: {case.truth}.")
    world.say(rng.choice([
        f'{hero.id} and {sidekick.id} checked the place again and saw how the mistake fit together.',
        f"Once they understood it, {hero.id} and {sidekick.id} smiled at the rival and asked for a fresh start.",
        f"The team followed the clue back to the source, and the whole misunderstanding became simple.",
        f"With the puzzle solved, the team could explain everything without shouting.",
    ]))
    world.para()
    world.say(rng.choice([
        f'The reconciliation was {params.reconciliation}: {case.repair}.',
        f"At last, there was {params.reconciliation}. {case.repair}.",
        f"That made room for {params.reconciliation}, and {case.repair}.",
        f"The heroes chose {params.reconciliation}, then {case.repair}.",
    ]))
    world.say(f"{hero.id} said, \"Thank you for helping us tell the truth.\"")
    world.say(f'{rival.id} replied, "{params.hero}, I am glad you checked before judging me."')
    world.say(f"By the end, {case.ending}.")
    hero.meters["rescues"] = 1
    sidekick.meters["rescues"] = 1
    rival.memes["forgiven"] = 1
    world.facts.update(hero=hero, sidekick=sidekick, rival=rival, scene=scene, case=case, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story about {f['hero'].id}, {f['case'].missing}, and the mistaken blame on {f['rival'].id}.",
        f"Tell a child-friendly action story at {f['scene'].place} where a twist reveals what happened to the missing item.",
        f"End with reconciliation after {f['hero'].id} and {f['sidekick'].id} discover the real cause.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"What was missing at {f['scene'].place}?",
            answer=f"{case.missing.capitalize()} was missing, so {f['hero'].id} and {f['sidekick'].id} had to investigate.",
        ),
        QAItem(
            question=f"Why did people think {f['rival'].id} caused the problem?",
            answer=f"People blamed {f['rival'].id} because {case.accusation}. That guess was loud, but it was not proof.",
        ),
        QAItem(
            question=f"What first search did {f['hero'].id} try before the twist?",
            answer=f"{f['hero'].id} {case.early_action}, but {case.early_result}. The first idea did not solve the case.",
        ),
        QAItem(
            question=f"Which clue revealed the truth?",
            answer=f"The twist came from {case.twist_clue}. It showed that {case.truth}.",
        ),
        QAItem(
            question=f"How did the story end after reconciliation?",
            answer=f"The heroes chose {params.reconciliation}, and {case.repair}. By the end, {case.ending}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What makes a superhero story feel fair and kind?",
            answer="A fair superhero story checks facts, protects people from unfair blame, and fixes mistakes with apology and teamwork.",
        ),
        QAItem(
            question="Why can a twist help solve a mystery?",
            answer="A twist can reveal a clue that changes the meaning of earlier events. That helps the heroes understand what really happened.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting, explain the truth, and repair trust so they can work together again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)), "", "== story qa =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.kind}/{e.type}) meters={e.meters} memes={e.memes}")
    case: Case = world.facts["case"]
    lines.append(f"  missing={case.missing}")
    lines.append(f"  truth={case.truth}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(place="rooftop", hero="Nova", sidekick="Pip", rival="Captain Crumb", twist="hidden_help", reconciliation="apology", seed=11),
    StoryParams(place="museum", hero="Bolt", sidekick="Mica", rival="Mirror Moth", twist="misread_clue", reconciliation="teamwork", seed=22),
    StoryParams(place="park", hero="Ruby", sidekick="Tess", rival="Sir Snap", twist="wrong_shadow", reconciliation="shared_laugh", seed=33),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, hero, rival in combos:
            print(f"  {place:8} {hero:8} {rival}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples, seen, attempts = [], set(), 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)
        )
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header="### curated story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
