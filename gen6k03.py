"""
gen6k03.py - Kernel Pack #03 for the gen6 engine.

Built by following the AGENTS.md gen6 workflow: the top ~70 missing kernels were
sampled from the dataset (via `coverage.py --missing` + a usage scan), their real
argument shapes studied, then implemented here.

Design notes (informed by the sampled shapes):
- Real calls are messy and frequently capitalize objects (`Break(Vase)`,
  `Build(Stack, block)`), so capitalized undefined names arrive as concept
  *strings*, not `Physical` entities. To stay robust these kernels take untyped
  `*args` and branch on whether each arg is a character `Entity`.
- Coherence still works: `ctx.say(subject)` is pronoun-aware, and the AST
  coherence pass keys off character-name args regardless of typing.
- Many verbs accept an implicit subject (the protagonist) when no character is
  passed (`Explore(park)` -> "<hero> explored the park").
"""

from __future__ import annotations

from typing import Any

from gen6 import (
    REGISTRY,
    World,
    Entity,
    Trace,
    NLGUtils,
    to_phrase,
    state_to_phrase,
    action_to_phrase,
    event_to_phrase,
    child_sentences,
    coherent,
    meta_story,
    is_meta_call,
)


# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------

def _is_char(x: Any) -> bool:
    return isinstance(x, Entity) and x.kind == "character"


def _split(args):
    chars = [a for a in args if _is_char(a)]
    rest = [a for a in args if not _is_char(a)]
    return chars, rest


_TARGET_KEYS = ("to", "for", "about", "with", "target", "object", "content",
                "destination", "reason", "request", "into", "method", "source")


def _kw_targets(kw: dict):
    out = []
    for k in _TARGET_KEYS:
        if k in kw and kw[k] is not None:
            out.append(kw[k])
    return out


def _phrases(values):
    out = []
    for v in values:
        p = str(v) if _is_char(v) else to_phrase(v)
        if p:
            out.append(p)
    return out


def _cap(s: str) -> str:
    return s[0].upper() + s[1:] if s else s


def _register(name: str, fn) -> None:
    fn.__name__ = name
    REGISTRY.kernel(name)(fn)


# ---------------------------------------------------------------------------
# factories
# ---------------------------------------------------------------------------

def transitive(name, past, *, solo="something", joy=0.0, love=0.0,
               wisdom=0.0, pride=0.0, prep=""):
    """Subject `past` object(s). Subject is the first character arg or the
    protagonist; remaining characters + objects + select kwargs are the object."""
    def fn(ctx: World, *args, **kw):
        chars, rest = _split(args)
        actor = chars[0] if chars else ctx.actor
        # Dual use: the same name is often a full multi-phase structure
        # (e.g. Care(Lily, state=..., process=..., outcome=...)). Route those to
        # the shared meta builder instead of collapsing to a single verb.
        if actor is not None and is_meta_call(kw):
            m = meta_story(ctx, actor, kw)
            if m:
                return m
        targets = _phrases(chars[1:]) + _phrases(rest) + _phrases(_kw_targets(kw))
        obj = NLGUtils.join_list(targets)
        if actor is not None:
            ctx.actor = actor
            if joy:
                actor.add_meme("Joy", joy)
            if love:
                actor.add_meme("Love", love)
            if wisdom:
                actor.add_meme("Wisdom", wisdom)
            if pride:
                actor.add_meme("Pride", pride)
            s = ctx.say(actor)
            tail = (prep + " " if prep else "") + obj
            return f"{s} {past} {tail}.".replace("  ", " ") if obj else f"{s} {past} {solo}."
        if obj:
            return f"Someone {past} {(prep + ' ') if prep else ''}{obj}."
        return f"{_cap(name.lower())} happened."
    _register(name, fn)


def intransitive(name, past, *, joy=0.0, sadness=0.0, love=0.0):
    """Subject `past` (no object). Multiple character args share the subject."""
    def fn(ctx: World, *args, **kw):
        chars, rest = _split(args)
        if is_meta_call(kw):
            hero = chars[0] if chars else ctx.actor
            if hero is not None:
                m = meta_story(ctx, hero, kw)
                if m:
                    return m
        actors = chars if chars else ([ctx.actor] if ctx.actor else [])
        for a in actors:
            if joy:
                a.add_meme("Joy", joy)
            if sadness:
                a.add_meme("Sadness", sadness)
            if love:
                a.add_meme("Love", love)
        if actors:
            ctx.actor = actors[0]
            if len(actors) == 1:
                subj = ctx.say(actors[0])
            else:
                subj = NLGUtils.join_list([str(a) for a in actors])
            return f"{subj} {past}."
        subj = NLGUtils.join_list(_phrases(rest)) or "everyone"
        return f"{_cap(subj)} {past}."
    _register(name, fn)


def emotion(name, template, *, meme=None, amount=1.0, solo=None):
    """Emotion/state. `template` uses {s} for the subject; `solo` is used when no
    subject is available (concept usage like `Happiness(Family)`)."""
    def fn(ctx: World, *args, **kw):
        chars, rest = _split(args)
        actor = chars[0] if chars else ctx.actor
        if actor is not None and is_meta_call(kw):
            m = meta_story(ctx, actor, kw)
            if m:
                return m
        if actor is not None:
            ctx.actor = actor
            if meme:
                actor.add_meme(meme, amount)
            return template.format(s=ctx.say(actor))
        subj = NLGUtils.join_list(_phrases(rest)) or "everyone"
        return (solo or template).format(s=_cap(subj))
    _register(name, fn)


def event(name, past):
    """Object-as-subject event: `Break(toy)` -> "The toy broke."."""
    def fn(ctx: World, *args, **kw):
        chars, rest = _split(args)
        if rest:
            return f"{_cap(to_phrase(rest[0]))} {past}."
        if chars:
            return f"{ctx.say(chars[0])} {past}."
        return f"Something {past}."
    _register(name, fn)


# ---------------------------------------------------------------------------
# transitive verbs
# ---------------------------------------------------------------------------

transitive("Build", "built", solo="something", joy=0.2)
transitive("Open", "opened")
transitive("Draw", "drew", joy=0.2)
transitive("Catch", "caught")
transitive("Take", "took")
transitive("Make", "made", joy=0.2)
transitive("Use", "used")
transitive("Gather", "gathered")
transitive("Offer", "offered", love=0.2)
transitive("Call", "called")
transitive("Invite", "invited", joy=0.2)
transitive("Praise", "praised", solo="everyone", joy=0.3)
transitive("Talk", "talked about", solo="for a while", prep="")
transitive("Learn", "learned about", solo="something new", wisdom=1.0)
transitive("Ride", "rode", joy=0.2)
transitive("Push", "pushed")
transitive("Hide", "hid", solo="away")
transitive("Explore", "explored", solo="all around", joy=0.2)
transitive("Chase", "chased", joy=0.2)
transitive("Reveal", "revealed")
transitive("Meet", "met")
transitive("Repair", "repaired", pride=0.3)
transitive("Fix", "fixed", pride=0.3)
transitive("Wish", "wished for", solo="something special")
transitive("Dream", "dreamed about", solo="wonderful things")
transitive("Care", "cared for", love=0.3)
transitive("Reward", "was rewarded with", solo="a treat")
transitive("Aid", "helped", love=0.3)
transitive("Trust", "trusted", solo="completely")
transitive("Question", "asked about", solo="a question")
transitive("Observation", "noticed")
transitive("Refusal", "refused", solo="firmly")


# ---------------------------------------------------------------------------
# intransitive verbs
# ---------------------------------------------------------------------------

intransitive("Smile", "smiled", joy=0.3)
intransitive("Listen", "listened carefully")
intransitive("Rest", "rested for a while")
intransitive("Sleep", "fell fast asleep")
intransitive("Laughter", "laughed and laughed", joy=0.5)
intransitive("Celebrate", "celebrated", joy=0.6)
intransitive("Celebration", "celebrated together", joy=0.6)
intransitive("Escape", "got away safely")
intransitive("Growth", "grew up a little")
intransitive("Arrival", "arrived")


# ---------------------------------------------------------------------------
# emotions / states
# ---------------------------------------------------------------------------

emotion("Happiness", "{s} was full of happiness.", meme="Joy", amount=1.0,
        solo="{s} were full of happiness.")
emotion("Excitement", "{s} could hardly wait.", meme="Joy", amount=0.6)
emotion("Relief", "{s} felt a wave of relief.", meme="Relief", amount=1.0)
emotion("Kindness", "{s} was very kind.", meme="Love", amount=0.3)
emotion("Pain", "{s} was in pain.", meme="Sadness", amount=0.5,
        solo="{s} hurt.")
emotion("Anticipation", "{s} could hardly wait.", meme="Joy", amount=0.3)
emotion("Acceptance", "{s} came to accept it.", meme="Wisdom", amount=0.3)
emotion("Love", "{s} felt full of love.", meme="Love", amount=1.0,
        solo="Everyone loved {s}.")


# ---------------------------------------------------------------------------
# object events
# ---------------------------------------------------------------------------

event("Break", "broke")
event("Fall", "fell down")


# ---------------------------------------------------------------------------
# concept / situation kernels (custom rendering)
# ---------------------------------------------------------------------------

def Catalyst(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    thing = NLGUtils.join_list(_phrases(rest) + _phrases(_kw_targets(kw)))
    if chars and thing:
        ctx.actor = chars[0]
        return f"Then {ctx.say(chars[0])} noticed {thing}."
    if thing:
        return f"Then, {thing} changed everything."
    return "Then, something happened that changed everything."


def Obstacle(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    thing = NLGUtils.join_list(_phrases(rest)) or "a problem"
    return f"But {thing} stood in the way."


def Threat(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    thing = NLGUtils.join_list(_phrases(rest) + [str(c) for c in chars[1:]])
    if chars:
        chars[0].add_meme("Fear", 0.5)
        ctx.actor = chars[0]
        if thing:
            return f"{ctx.say(chars[0])} was threatened by {thing}."
    if thing:
        return f"There was danger from {thing}."
    return "Danger was near."


def Sight(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    thing = NLGUtils.join_list(_phrases(rest)) or "something"
    if chars:
        ctx.actor = chars[0]
        return f"{ctx.say(chars[0])} saw {thing}."
    return f"There was {thing} to see."


def Failure(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    if chars:
        ctx.actor = chars[0]
        chars[0].add_meme("Sadness", 0.4)
        return f"{ctx.say(chars[0])} did not succeed."
    return "It did not work out."


def Problem(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    detail = NLGUtils.join_list(_phrases(rest) + _phrases(_kw_targets(kw)))
    if chars:
        ctx.actor = chars[0]
        return f"{ctx.say(chars[0])} had a problem" + (f" with {detail}." if detail else ".")
    if detail:
        return f"There was a problem with {detail}."
    return "There was a problem."


def Habit(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    what = NLGUtils.join_list([action_to_phrase(r) for r in rest])
    if chars:
        ctx.actor = chars[0]
        return f"{ctx.say(chars[0])} made a habit of it." if not what \
            else f"{ctx.say(chars[0])} got into the habit of {what}."
    return "It became a regular habit."


def Emotion(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    state = kw.get("state")
    feeling = state_to_phrase(state) if state is not None else \
        NLGUtils.join_list([state_to_phrase(r) for r in rest])
    if chars:
        ctx.actor = chars[0]
        return f"{ctx.say(chars[0])} felt {feeling}." if feeling \
            else f"{ctx.say(chars[0])} was overcome with emotion."
    return f"There was a feeling of {feeling}." if feeling else "Emotions ran high."


def Guidance(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    if chars and is_meta_call(kw):
        m = meta_story(ctx, chars[0], kw)
        if m:
            return m
    if chars:
        ctx.actor = chars[0]
        other = _phrases(chars[1:]) + _phrases(_kw_targets(kw))
        if other:
            return f"{ctx.say(chars[0])} showed {NLGUtils.join_list(other)} the way."
        return f"{ctx.say(chars[0])} offered some guidance."
    return "There was helpful guidance."


def Transform(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    items = _phrases(rest) + _phrases(_kw_targets(kw))
    subject = items[0] if items else (str(chars[0]) if chars else "it")
    result = items[1] if len(items) > 1 else None
    if result:
        return f"{_cap(subject)} turned into {result}."
    return f"{_cap(subject)} was transformed."


def Bond(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    if len(chars) >= 2:
        chars[0].add_meme("Friendship", 1.0)
        chars[0].add_link("Friendship", chars[1].name)
        ctx.actor = chars[0]
        return f"{chars[0]} and {NLGUtils.join_list([str(c) for c in chars[1:]])} formed a close bond."
    if chars:
        return f"{chars[0]} formed a special bond."
    return "A special bond formed between them."


def Advice(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    content = NLGUtils.join_list(_phrases(_kw_targets(kw)) + _phrases(rest))
    if chars:
        ctx.actor = chars[0]
        listener = str(chars[1]) if len(chars) > 1 else None
        who = f" {listener}" if listener else ""
        return f"{ctx.say(chars[0])} gave{who} some advice" + (f" about {content}." if content else ".")
    return "There was some good advice."


for _name, _fn in [("Catalyst", Catalyst), ("Obstacle", Obstacle), ("Threat", Threat),
                   ("Sight", Sight), ("Failure", Failure), ("Problem", Problem),
                   ("Habit", Habit), ("Emotion", Emotion), ("Guidance", Guidance),
                   ("Transform", Transform), ("Bond", Bond), ("Advice", Advice)]:
    REGISTRY.kernel(_name)(_fn)


# ---------------------------------------------------------------------------
# meta / multi-phase kernels (keyword phases, like Quest in gen6k01)
# ---------------------------------------------------------------------------

@REGISTRY.kernel("Adventure")
def Adventure(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is None:
        return "It was a grand adventure."
    ctx.actor = hero
    return meta_story(ctx, hero, kw, fallback=f"{hero.name} set off on a great adventure.")


@REGISTRY.kernel("Process")
@REGISTRY.kernel("Action")
def Process(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is not None and is_meta_call(kw):
        m = meta_story(ctx, hero, kw)
        if m:
            return m
    steps = kw.get("process") or kw.get("action") or kw.get("actions")
    # A process is a sequence of sub-actions; emit each child as its own sentence.
    sents = []
    for piece in [steps] + list(rest):
        cs = child_sentences(piece)
        if cs is not None:
            sents += cs
        elif piece is not None:
            phrase = action_to_phrase(piece)
            if phrase and hero is not None:
                sents.append(f"{hero.name} {phrase}.")
            elif phrase:
                sents.append(f"{_cap(phrase)}.")
    if not sents and hero is not None:
        sents.append(f"{hero.name} got to work.")
    if hero is not None:
        ctx.actor = hero
        return coherent(ctx, hero, sents)
    return " ".join(sents) or "Things happened."


@REGISTRY.kernel("Cooperation")
def Cooperation(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    if chars:
        ctx.actor = chars[0]
        chars[0].add_meme("Friendship", 0.5)
        who = NLGUtils.join_list([str(c) for c in chars]) if len(chars) > 1 else str(chars[0])
        sents = [f"{who} worked together."]
        body = meta_story(ctx, chars[0], kw)
        if body:
            sents.append(body)
        return coherent(ctx, chars[0], sents)
    return "Everyone worked together."


if __name__ == "__main__":
    # Load every pack so cross-pack kernels (e.g. Routine/Curiosity in gen6k01)
    # resolve — testing a pack in isolation would otherwise miss siblings.
    import gen6registry  # noqa: F401
    from gen6 import generate

    tests = [
        "Lily(Character, girl)\nBuild(castle)\nOpen(Lily, box)\nBreak(Vase)",
        "Tim(Character, boy)\nMom(Character, mother)\nPraise(Mom, Tim)\nSmile(Tim, Mom)\nHappiness(Tim)",
        "Max(Character, boy)\nChase(Max, ball)\nFall(kite)\nBond(Max, Sue)",
        "Jane(Character, girl)\nAdventure(Jane, state=Routine + Curiosity, catalyst=Threat, process=Explore(forest) + Find(treasure), outcome=Happy)",
    ]
    for i, t in enumerate(tests, 1):
        print(f"--- TEST {i} ---")
        print(generate(t))
        print()
