"""
gen6k04.py - Kernel Pack #04 for the gen6 engine.

Built by following the AGENTS.md gen6 workflow: the next ~70 highest-frequency
missing kernels (after the gen6k03 batch) were sampled from the dataset with a
shape scan, their real argument shapes studied, then implemented here.

This pack leans on the factory helpers already defined in `gen6k03.py`
(`transitive`, `intransitive`, `emotion`, plus the `_split` / `_phrases` /
`_kw_targets` utilities) so the simple verb/emotion kernels stay one line each,
and adds hand-written variants for the kernels whose real shapes need bespoke
rendering (object-first events, multi-character reunions, child-trace wrappers
like `Outcome`/`Result`/`Consequence`, and the meta/multi-phase structures
`Game`, `Trip`, `Learning`, `Change`, `Collaboration`, ...).

Design notes (from the sampled shapes):
- Calls are frequently object-first with no leading character
  (`Travel(zoo)`, `Need(Light)`, `Wear(dress)`); these fall back to the current
  protagonist (`ctx.actor`) when present, else read as a subjectless sentence.
- Capitalised undefined names arrive as concept *strings*, so kernels branch on
  whether each arg is a character `Entity` (via `_split`).
- Phase kwargs (`state=`, `process=`, `outcome=`, ...) route to the shared
  `meta_story` builder so a "simple" kernel called richly still tells a story.
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
    child_sentences,
    coherent,
    meta_story,
    is_meta_call,
    _lead_join,
)

# Reuse the gen6k03 factories + helpers instead of duplicating ~120 lines.
from gen6k03 import (
    transitive,
    intransitive,
    emotion,
    _split,
    _phrases,
    _kw_targets,
    _cap,
    _is_char,
)


def _register(name: str, fn) -> None:
    fn.__name__ = name
    REGISTRY.kernel(name)(fn)


def _vals(kw: dict, *keys: str):
    """First non-None value among the given kwargs (in order)."""
    for k in keys:
        if k in kw and kw[k] is not None:
            return kw[k]
    return None


# ---------------------------------------------------------------------------
# Simple transitive verbs  (subject `past` object[s])
# ---------------------------------------------------------------------------

transitive("Wear", "put on", solo="something nice", joy=0.1)
transitive("Carry", "carried", solo="it along")
transitive("Buy", "bought", solo="something", joy=0.2)
transitive("Read", "read", solo="a story", wisdom=0.2)
transitive("Collect", "collected", solo="lots of things")
transitive("Cut", "cut", solo="it carefully")
transitive("Hold", "held", solo="it tight", love=0.1)
transitive("Hit", "hit", solo="it")
transitive("Touch", "touched", solo="it gently")
transitive("Pull", "pulled", solo="hard")
transitive("Mix", "mixed", solo="everything together")
transitive("Bake", "baked", solo="a treat", joy=0.2)
transitive("Retrieve", "fetched", solo="it back", joy=0.1)
transitive("Seek", "looked for", solo="far and wide")
transitive("Create", "made", solo="something special", joy=0.2, pride=0.2)
transitive("Protect", "protected", solo="everyone", love=0.3)
transitive("Knock", "knocked over", solo="something")
transitive("Place", "placed", solo="it down")
transitive("Release", "let go of", solo="it")
transitive("Taste", "tasted", solo="it", joy=0.1)
transitive("Enter", "went into", solo="inside")
transitive("Practice", "practiced", solo="hard", pride=0.2)
transitive("Pretend", "pretended to be", solo="someone else", joy=0.2)
transitive("Accept", "accepted", solo="it", wisdom=0.2)
transitive("Refuse", "refused", solo="firmly")
transitive("Forget", "forgot", solo="something")
transitive("Remember", "remembered", solo="everything", wisdom=0.2)
transitive("Explain", "explained", solo="everything")
transitive("Reassure", "reassured", solo="everyone", love=0.3)
transitive("Assist", "helped", solo="out", love=0.3)
transitive("Support", "supported", solo="everyone", love=0.3)
transitive("Wait", "waited for", solo="patiently")
transitive("Follow", "followed", solo="along")


# ---------------------------------------------------------------------------
# Custom verbs / events whose real shapes need bespoke handling
# ---------------------------------------------------------------------------

def Need(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    if actor is not None and is_meta_call(kw):
        m = meta_story(ctx, actor, kw)
        if m:
            return m
    want = NLGUtils.join_list(_phrases(chars[1:]) + _phrases(rest) + _phrases(_kw_targets(kw)))
    if actor is not None:
        ctx.actor = actor
        return f"{ctx.say(actor)} needed {want}." if want else f"{ctx.say(actor)} needed some help."
    return f"There was a need for {want}." if want else "Something was needed."


def Sing(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    song = NLGUtils.join_list(_phrases(rest) + _phrases([kw.get("song")] if kw.get("song") else []))
    singers = chars if chars else ([ctx.actor] if ctx.actor else [])
    if singers:
        for s in singers:
            s.add_meme("Joy", 0.3)
        ctx.actor = singers[0]
        subj = ctx.say(singers[0]) if len(singers) == 1 else NLGUtils.join_list([str(s) for s in singers])
        return f"{subj} sang {song}." if song else f"{subj} sang a happy song."
    return f"There was singing of {song}." if song else "There was a happy song."


def Dance(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    music = NLGUtils.join_list(_phrases(rest) + _phrases([kw.get("music")] if kw.get("music") else []))
    dancers = chars if chars else ([ctx.actor] if ctx.actor else [])
    if dancers:
        for d in dancers:
            d.add_meme("Joy", 0.4)
        ctx.actor = dancers[0]
        subj = ctx.say(dancers[0]) if len(dancers) == 1 else NLGUtils.join_list([str(d) for d in dancers])
        return f"{subj} danced to {music}." if music else f"{subj} danced and danced."
    return f"There was dancing to {music}." if music else "There was lots of dancing."


def Hurt(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else None
    part = _vals(kw, "body", "part")
    pieces = _phrases(rest) + ([to_phrase(part)] if part is not None else [])
    thing = NLGUtils.join_list(pieces)
    if actor is not None:
        ctx.actor = actor
        actor.add_meme("Sadness", 0.4)
        return f"{ctx.say(actor)} hurt {thing}." if thing else f"{ctx.say(actor)} got hurt."
    if thing:
        return f"{_cap(thing)} got hurt."
    return "Someone got hurt."


def Sit(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    with_who = kw.get("with")
    where = NLGUtils.join_list(_phrases(rest))
    if actor is not None:
        ctx.actor = actor
        if with_who is not None:
            return f"{ctx.say(actor)} sat down with {to_phrase(with_who)}."
        return f"{ctx.say(actor)} sat down on {where}." if where else f"{ctx.say(actor)} sat down."
    return f"They sat down on {where}." if where else "They sat down for a rest."


def Travel(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    dest = _vals(kw, "destination", "to", "inside")
    place = to_phrase(dest) if dest is not None else NLGUtils.join_list(_phrases(rest))
    travelers = chars if chars else ([ctx.actor] if ctx.actor else [])
    if travelers:
        for t in travelers:
            t.add_meme("Joy", 0.1)
        ctx.actor = travelers[0]
        subj = ctx.say(travelers[0]) if len(travelers) == 1 else NLGUtils.join_list([str(t) for t in travelers])
        return f"{subj} traveled to {place}." if place else f"{subj} set off on a journey."
    return f"They traveled to {place}." if place else "Off on a journey they went."


def Continue(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    sents = []
    for r in rest:
        cs = child_sentences(r)
        if cs is not None:
            sents += cs
    if actor is not None:
        ctx.actor = actor
        lead = f"{ctx.say(actor)} kept going."
    else:
        lead = "And so it carried on."
    return coherent(ctx, actor, [lead] + sents) if sents else lead


def Stuck(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else None
    if actor is not None and is_meta_call(kw):
        m = meta_story(ctx, actor, kw)
        if m:
            return m
    loc = kw.get("location")
    where = NLGUtils.join_list(_phrases(rest) + ([to_phrase(loc)] if loc is not None else []))
    if actor is not None:
        ctx.actor = actor
        actor.add_meme("Fear", 0.3)
        return f"{ctx.say(actor)} got stuck in {where}." if where else f"{ctx.say(actor)} was stuck."
    if where:
        return f"It got stuck in {where}."
    return "It was stuck fast."


def Safety(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    if chars:
        for c in chars:
            c.add_meme("Relief", 0.3)
        ctx.actor = chars[0]
        who = NLGUtils.join_list([str(c) for c in chars])
        verb = "was" if len(chars) == 1 else "were"
        return f"{who} {verb} safe and sound."
    place = NLGUtils.join_list(_phrases(rest))
    return f"It was safe by {place}." if place else "Everyone was safe and sound."


def Appreciation(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    target = _phrases(chars[1:]) + _phrases(rest) + _phrases([kw.get("target")] if kw.get("target") else [])
    t = NLGUtils.join_list(target)
    if actor is not None:
        ctx.actor = actor
        actor.add_meme("Love", 0.3)
        return f"{ctx.say(actor)} was grateful for {t}." if t else f"{ctx.say(actor)} felt very thankful."
    return f"Everyone was grateful for {t}." if t else "There was a feeling of gratitude."


def Forgiveness(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    if chars and is_meta_call(kw):
        m = meta_story(ctx, chars[0], kw)
        if m:
            return m
    if len(chars) >= 2:
        chars[0].add_meme("Love", 0.3)
        ctx.actor = chars[0]
        return f"{chars[0]} forgave {NLGUtils.join_list([str(c) for c in chars[1:]])}."
    to = kw.get("to")
    if chars and to is not None:
        chars[0].add_meme("Love", 0.3)
        ctx.actor = chars[0]
        return f"{chars[0]} forgave {to_phrase(to)}."
    if chars:
        ctx.actor = chars[0]
        return f"{ctx.say(chars[0])} chose to forgive."
    return "And all was forgiven."


def Healing(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    if actor is not None and is_meta_call(kw):
        m = meta_story(ctx, actor, kw)
        if m:
            return m
    target = _phrases(chars[1:]) + _phrases(rest) + _phrases([kw.get("target")] if kw.get("target") else [])
    t = NLGUtils.join_list(target)
    if actor is not None:
        ctx.actor = actor
        actor.add_meme("Relief", 0.3)
        return f"{ctx.say(actor)} helped {t} heal." if t else f"{ctx.say(actor)} slowly got better."
    if t:
        return f"{_cap(t)} began to heal."
    return "Slowly, everything healed."


def Recovery(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    if actor is not None and is_meta_call(kw):
        m = meta_story(ctx, actor, kw)
        if m:
            return m
    if actor is not None:
        ctx.actor = actor
        actor.add_meme("Relief", 0.4)
        regained = kw.get("regained")
        if regained is not None:
            return f"{ctx.say(actor)} got {to_phrase(regained)} back."
        return f"{ctx.say(actor)} made a full recovery."
    return "Things got back to normal again."


def Memory(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    if actor is not None and is_meta_call(kw):
        m = meta_story(ctx, actor, kw)
        if m:
            return m
    thing = _phrases(chars[1:]) + _phrases(rest) + _phrases([kw.get("recall")] if kw.get("recall") else [])
    t = NLGUtils.join_list(thing)
    if actor is not None:
        ctx.actor = actor
        actor.add_meme("Joy", 0.2)
        return f"{ctx.say(actor)} would always remember {t}." if t else f"{ctx.say(actor)} had a happy memory to keep."
    return f"It was a memory of {t} to treasure." if t else "It was a memory to treasure forever."


def Value(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    items = _phrases(rest) + _phrases([kw.get("own")] if kw.get("own") else [])
    t = NLGUtils.join_list(items)
    if actor is not None and t:
        ctx.actor = actor
        return f"{ctx.say(actor)} treasured {t}."
    if t:
        return f"{_cap(t)} was something to treasure."
    return "It was truly precious."


def Magic(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    if actor is not None and is_meta_call(kw):
        m = meta_story(ctx, actor, kw)
        if m:
            return m
    if rest:
        return f"{_cap(to_phrase(rest[0]))} sparkled with magic."
    if actor is not None:
        ctx.actor = actor
        return f"{ctx.say(actor)} felt the magic all around."
    return "Magic was in the air."


def Noise(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    if chars:
        ctx.actor = chars[0]
        return f"{chars[0]} made a loud noise."
    src = kw.get("source")
    maker = to_phrase(src) if src is not None else (to_phrase(rest[0]) if rest else "")
    return f"{_cap(maker)} made a loud noise." if maker else "There was a loud noise."


def Careful(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    focus = _vals(kw, "focus", "next")
    if actor is not None:
        ctx.actor = actor
        cs = child_sentences(focus) if focus is not None else None
        if cs:
            return coherent(ctx, actor, [f"{ctx.say(actor)} was very careful."] + cs)
        return f"{ctx.say(actor)} was very careful."
    thing = NLGUtils.join_list(_phrases(rest))
    return f"Everyone was careful with {thing}." if thing else "Everyone was very careful."


def Not(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    state = rest[0] if rest else None
    if chars:
        ctx.actor = chars[0]
        if state is not None:
            return f"{ctx.say(chars[0])} was not {state_to_phrase(state)}."
        return f"{ctx.say(chars[0])} would not."
    if state is not None:
        cs = child_sentences(state)
        if cs is not None:
            return "It was best not to do that."
        return f"It was not {state_to_phrase(state)}."
    return "No, not at all."


# ---------------------------------------------------------------------------
# Emotions / states
# ---------------------------------------------------------------------------

emotion("Confidence", "{s} felt confident.", meme="Pride", amount=0.5,
        solo="There was a feeling of confidence.")
emotion("Compassion", "{s} felt a deep compassion.", meme="Love", amount=0.4,
        solo="There was great compassion.")


# ---------------------------------------------------------------------------
# Child-trace wrappers: Outcome / Result / Consequence
# ---------------------------------------------------------------------------

def _wrapper(name: str, lead: str, *, sadness: float = 0.0, joy: float = 0.0):
    def fn(ctx: World, *args, **kw):
        chars, rest = _split(args)
        hero = chars[0] if chars else ctx.actor
        sents = []
        had_trace = False
        for v in list(args) + list(kw.values()):
            cs = child_sentences(v)
            if cs is not None:
                sents += cs
                had_trace = True
        if hero is not None:
            ctx.actor = hero
            if joy:
                hero.add_meme("Joy", joy)
            if sadness:
                hero.add_meme("Sadness", sadness)
        if had_trace and sents:
            sents = [_lead_join(lead, sents[0])] + sents[1:]
            return coherent(ctx, hero, sents)
        # No child traces: render bare concepts as a state.
        items = _phrases(rest) + _phrases([v for v in kw.values()])
        joined = NLGUtils.join_list(items)
        if hero is not None and joined:
            return f"{lead}{ctx.say(hero)} was {joined}."
        if joined:
            return f"{lead}everything was {joined}."
        return f"{lead}everything worked out."
    _register(name, fn)


_wrapper("Outcome", "In the end, ", joy=0.4)
_wrapper("Result", "As a result, ")
_wrapper("Consequence", "Because of that, ", sadness=0.3)


# ---------------------------------------------------------------------------
# Communication / social
# ---------------------------------------------------------------------------

def Explanation(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    extra = _phrases([_vals(kw, "about", "clarify", "details", "joke", "purpose")])
    detail = _phrases(chars[1:]) + _phrases(rest) + _phrases(_kw_targets(kw)) + extra
    d = NLGUtils.join_list([x for x in detail if x])
    if actor is not None:
        ctx.actor = actor
        return f"{ctx.say(actor)} explained about {d}." if d else f"{ctx.say(actor)} explained everything."
    return f"There was an explanation about {d}." if d else "It was all explained."


def Dialogue(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    topic = _vals(kw, "topic", "question", "about")
    if len(chars) >= 2:
        ctx.actor = chars[0]
        t = f" about {to_phrase(topic)}" if topic is not None else ""
        return f"{NLGUtils.join_list([str(c) for c in chars])} talked{t}."
    if chars:
        ctx.actor = chars[0]
        for r in rest:
            cs = child_sentences(r)
            if cs:
                return coherent(ctx, chars[0], cs)
        t = f" about {to_phrase(topic)}" if topic is not None else ""
        return f"{ctx.say(chars[0])} spoke up{t}."
    return "They had a little chat."


def Invitation(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    to = _vals(kw, "to", "destination", "request")
    guests = _phrases(chars[1:])
    item = _phrases(rest) + _phrases([kw.get("item")] if kw.get("item") else [])
    if actor is not None:
        ctx.actor = actor
        actor.add_meme("Joy", 0.2)
        if guests:
            tail = f" to {to_phrase(to)}" if to is not None else (
                f" to {NLGUtils.join_list(item)}" if item else "")
            return f"{ctx.say(actor)} invited {NLGUtils.join_list(guests)}{tail}."
        if to is not None:
            return f"{ctx.say(actor)} sent out an invitation to {to_phrase(to)}."
        if item:
            return f"{ctx.say(actor)} sent out an invitation to {NLGUtils.join_list(item)}."
        return f"{ctx.say(actor)} sent out an invitation."
    return "An invitation was sent out."


def Denial(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    obj = kw.get("object")
    to = kw.get("to")
    things = NLGUtils.join_list(_phrases(rest) + ([to_phrase(obj)] if obj is not None else []))
    if actor is not None:
        ctx.actor = actor
        if things and to is not None:
            return f"{ctx.say(actor)} would not give {things} to {to_phrase(to)}."
        if things:
            return f"{ctx.say(actor)} said no to {things}."
        return f"{ctx.say(actor)} said no."
    return "The answer was no."


def Permission(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    allow = kw.get("allow")
    if allow is not None:
        actor = chars[0] if chars else ctx.actor
        act = child_sentences(allow)
        if actor is not None:
            ctx.actor = actor
            if act:
                return coherent(ctx, actor, [f"{ctx.say(actor)} gave permission."] + act)
            return f"{ctx.say(actor)} allowed {to_phrase(allow)}."
        return f"Permission was given to {to_phrase(allow)}."
    if chars:
        ctx.actor = chars[0]
        item = NLGUtils.join_list(_phrases(rest))
        if item:
            return f"{chars[0]} was allowed to have {item}."
        return f"{chars[0]} was given permission."
    if rest:
        cs = child_sentences(rest[0])
        if cs:
            return " ".join(cs)
    return "Permission was granted."


def Intervention(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    action = _vals(kw, "action", "advise", "advice")
    if hero is not None:
        ctx.actor = hero
        cs = child_sentences(action) if action is not None else None
        if cs:
            return coherent(ctx, hero, [f"{ctx.say(hero)} stepped in to help."] + cs)
        helpers = _phrases(chars[1:]) + _phrases(rest)
        if helpers:
            return f"{ctx.say(hero)} stepped in with {NLGUtils.join_list(helpers)}."
        return f"{ctx.say(hero)} stepped in to help."
    return "Someone stepped in to help."


# ---------------------------------------------------------------------------
# Group / multi-character social kernels
# ---------------------------------------------------------------------------

def PlayTogether(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    place = NLGUtils.join_list(_phrases(rest))
    if chars:
        for c in chars:
            c.add_meme("Joy", 0.3)
            c.add_meme("Friendship", 0.2)
        ctx.actor = chars[0]
        tail = f" at {place}" if place else ""
        if len(chars) == 1:
            return f"{ctx.say(chars[0])} played happily{tail}."
        return f"{NLGUtils.join_list([str(c) for c in chars])} played together{tail}."
    return f"They all played together with {place}." if place else "They all played together."


def Reunion(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is not None and is_meta_call(kw):
        for c in chars:
            c.add_meme("Joy", 0.4)
        ctx.actor = hero
        subj = NLGUtils.join_list([str(c) for c in chars]) if chars else ctx.say(hero)
        body = meta_story(ctx, hero, kw)
        return coherent(ctx, hero, [f"{subj} were reunited at last."] + ([body] if body else []))
    if len(chars) >= 2:
        for c in chars:
            c.add_meme("Joy", 0.4)
        ctx.actor = chars[0]
        return f"{NLGUtils.join_list([str(c) for c in chars])} were happily reunited."
    if chars:
        ctx.actor = chars[0]
        chars[0].add_meme("Joy", 0.4)
        return f"{ctx.say(chars[0])} was reunited with everyone."
    return "There was a happy reunion."


def Collaboration(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    for c in chars:
        c.add_meme("Friendship", 0.3)
    who = NLGUtils.join_list([str(c) for c in chars]) if len(chars) > 1 else (str(chars[0]) if chars else None)
    # A `task=`/positional value may be a nested action Trace (render it as its own
    # sentence) or a bare concept (inline it after "worked together on ...").
    task_sents = []
    inline = []
    for v in rest + ([kw["task"]] if kw.get("task") is not None else []):
        cs = child_sentences(v)
        if cs is not None:
            task_sents += cs
        else:
            p = to_phrase(v)
            if p:
                inline.append(p)
    intro = f"{who} worked together" if who else "Everyone worked together"
    intro += f" on {NLGUtils.join_list(inline)}." if inline else "."
    if hero is not None:
        ctx.actor = hero
        body = meta_story(ctx, hero, kw)
        return coherent(ctx, hero, [intro] + task_sents + ([body] if body else []))
    return coherent(ctx, hero, [intro] + task_sents) if task_sents else intro


# ---------------------------------------------------------------------------
# Meta / multi-phase activities
# ---------------------------------------------------------------------------

def Game(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    name = to_phrase(rest[0]) if (rest and not isinstance(rest[0], Trace)) else None
    who = NLGUtils.join_list([str(c) for c in chars]) if chars else (ctx.say(hero) if hero else "They")
    for c in chars:
        c.add_meme("Joy", 0.3)
    if hero is not None:
        ctx.actor = hero
    intro = f"{who} played a game of {name}." if name else f"{who} played a fun game."
    if hero is not None and is_meta_call(kw):
        body = meta_story(ctx, hero, kw)
        return coherent(ctx, hero, [intro] + ([body] if body else []))
    return intro


def Trip(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    who = NLGUtils.join_list([str(c) for c in chars]) if chars else (ctx.say(hero) if hero else "Everyone")
    for c in chars:
        c.add_meme("Joy", 0.2)
    if hero is not None:
        ctx.actor = hero
    if hero is not None and is_meta_call(kw):
        body = meta_story(ctx, hero, kw)
        return coherent(ctx, hero, [f"{who} went on a trip."] + ([body] if body else []))
    dest = _vals(kw, "to", "destination")
    place = to_phrase(dest) if dest is not None else NLGUtils.join_list(_phrases(rest))
    return f"{who} went on a trip to {place}." if place else f"{who} went on a lovely trip."


def Learning(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is not None and is_meta_call(kw):
        m = meta_story(ctx, hero, kw)
        if m:
            return m
    topic = NLGUtils.join_list(_phrases(rest) + _phrases([kw.get("subject")] if kw.get("subject") else []))
    if hero is not None:
        ctx.actor = hero
        hero.add_meme("Wisdom", 1.0)
        return f"{ctx.say(hero)} learned about {topic}." if topic else f"{ctx.say(hero)} learned something new."
    return f"It was all about learning {topic}." if topic else "There was a lot to learn."


def Change(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    frm = kw.get("from")
    to = kw.get("to")
    if hero is not None and frm is not None and to is not None:
        ctx.actor = hero
        return f"{ctx.say(hero)} changed from {to_phrase(frm)} to {to_phrase(to)}."
    if hero is not None and is_meta_call(kw):
        m = meta_story(ctx, hero, kw)
        if m:
            return m
    if hero is not None:
        ctx.actor = hero
        beh = kw.get("behavior")
        if beh is not None:
            return f"{ctx.say(hero)} became more {to_phrase(beh)}."
        return f"{ctx.say(hero)} was not quite the same anymore."
    items = _phrases(rest)
    if len(items) >= 2:
        return f"{_cap(items[0])} changed into {items[1]}."
    return "And everything changed."


for _name, _fn in [
    ("Need", Need), ("Sing", Sing), ("Dance", Dance), ("Hurt", Hurt),
    ("Sit", Sit), ("Travel", Travel), ("Continue", Continue), ("Stuck", Stuck),
    ("Safety", Safety), ("Appreciation", Appreciation),
    ("Forgiveness", Forgiveness), ("Healing", Healing), ("Recovery", Recovery),
    ("Memory", Memory), ("Value", Value), ("Magic", Magic), ("Noise", Noise),
    ("Careful", Careful), ("Not", Not), ("Explanation", Explanation),
    ("Dialogue", Dialogue), ("Invitation", Invitation), ("Denial", Denial),
    ("Permission", Permission), ("Intervention", Intervention),
    ("PlayTogether", PlayTogether), ("Reunion", Reunion),
    ("Collaboration", Collaboration), ("Game", Game), ("Trip", Trip),
    ("Learning", Learning), ("Change", Change),
]:
    _register(_name, _fn)


if __name__ == "__main__":
    import gen6registry  # noqa: F401  (load sibling packs)
    from gen6 import generate

    tests = [
        "Lily(Character, girl)\nWear(Lily, dress)\nBuy(Lily, toy)\nRead(book)",
        "Tim(Character, boy)\nMom(Character, mother)\nTravel(Tim, Mom, destination=park)\nPlayTogether(Tim, Mom, park)",
        "Sam(Character, boy)\nHurt(knee)\nHealing(Sam)\nRecovery(Sam)",
        "Anna(Character, girl)\nBen(Character, boy)\nReunion(Anna, Ben)\nOutcome(Joy + Friendship(Anna, Ben))",
        "Lily(Character, girl)\nGame(HideSeek, seeker=Lily)\nTrip(Lily, to=zoo)\nLearning(Lily, subject=numbers)",
        "Max(Character, boy)\nChange(Max, to=Wise)\nForgiveness(Max, Lily)\nMagic(rock)",
    ]
    for i, t in enumerate(tests, 1):
        print(f"--- TEST {i} ---")
        print(generate(t))
        print()
