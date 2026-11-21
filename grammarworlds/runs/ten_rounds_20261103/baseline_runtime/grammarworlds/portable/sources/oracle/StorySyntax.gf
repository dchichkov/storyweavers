-- Stable application interface. English morphology/syntax live in the RGL.
abstract StorySyntax = {
  flags startcat = Output ;
  cat Output ; Sent ; Clause ; Nom ; Common ; Quality ; Action ;
      Verb ; TransVerb ; IntentVerb ; ReportVerb ; GiveVerb ; AskVerb ;
      Relation ; Manner ; Time ; Polarity ;
  fun
    Utter : Sent -> Output ;
    Say : Time -> Polarity -> Clause -> Sent ;
    AndS : Sent -> Sent -> Sent ;
    ButS : Sent -> Sent -> Sent ;
    BecauseS : Sent -> Sent -> Sent ;
    Past : Time ; Present : Time ; Positive : Polarity ; Negative : Polarity ;
    Pred : Nom -> Action -> Clause ;
    She : Nom ; He : Nom ; It : Nom ; They : Nom ;
    Def : Common -> Nom ; Indef : Common -> Nom ;
    DefPlural : Common -> Nom ; IndefPlural : Common -> Nom ;
    Mass : Common -> Nom ;
    Both : Nom -> Nom -> Nom ;
    Her : Common -> Nom ; His : Common -> Nom ; Their : Common -> Nom ;
    Modify : Quality -> Common -> Common ;
    LocateN : Common -> Manner -> Common ;
    V2 : Verb -> TransVerb ;
    V2Prep : Verb -> Relation -> TransVerb ;
    VV : Verb -> IntentVerb ;
    VS : Verb -> ReportVerb ;
    V3 : Verb -> GiveVerb ;
    V2V : Verb -> AskVerb ;
    Intrans : Verb -> Action ;
    Trans : TransVerb -> Nom -> Action ;
    Intend : IntentVerb -> Action -> Action ;
    Report : ReportVerb -> Sent -> Action ;
    Give : GiveVerb -> Nom -> Nom -> Action ;
    Ask : AskVerb -> Nom -> Action -> Action ;
    Be : Quality -> Action ;
    BeAt : Manner -> Action ;
    Can : Action -> Action ;
    WithAdv : Action -> Manner -> Action ;
    PP : Relation -> Nom -> Manner ;
}
