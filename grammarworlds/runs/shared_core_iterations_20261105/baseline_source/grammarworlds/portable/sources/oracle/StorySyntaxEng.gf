concrete StorySyntaxEng of StorySyntax = open SyntaxEng, ParadigmsEng in {
  lincat
    Output = Text ; Sent = S ; Clause = Cl ; Nom = NP ; Common = CN ;
    Quality = A ; Action = VP ; Verb = SyntaxEng.V ; TransVerb = SyntaxEng.V2 ;
    IntentVerb = SyntaxEng.VV ; ReportVerb = SyntaxEng.VS ; GiveVerb = SyntaxEng.V3 ; AskVerb = SyntaxEng.V2V ;
    Relation = SyntaxEng.Prep ; Manner = Adv ; Time = Tense ; Polarity = Pol ;
  lin
    Utter s = mkText s ;
    Say t p c = mkS t p c ;
    AndS a b = mkS and_Conj a b ;
    ButS a b = mkS (mkConj "but") a b ;
    BecauseS a b = mkS (SyntaxEng.mkAdv because_Subj b) a ;
    Past = pastTense ; Present = presentTense ;
    Positive = positivePol ; Negative = negativePol ;
    Pred n v = mkCl n v ;
    She = mkNP she_Pron ; He = mkNP he_Pron ;
    It = mkNP it_Pron ; They = mkNP they_Pron ;
    Def n = mkNP the_Det n ; Indef n = mkNP a_Det n ;
    DefPlural n = mkNP thePl_Det n ; IndefPlural n = mkNP aPl_Det n ;
    Mass n = mkNP n ;
    Both a b = mkNP and_Conj a b ;
    Her n = mkNP she_Pron n ; His n = mkNP he_Pron n ; Their n = mkNP they_Pron n ;
    Modify a n = mkCN a n ;
    LocateN n a = mkCN n a ;
    V2 v = mkV2 v ; V2Prep v p = mkV2 v p ;
    VV v = mkVV v ; VS v = mkVS v ; V3 v = mkV3 v ; V2V v = mkV2V v ;
    Intrans v = mkVP v ; Trans v n = mkVP v n ;
    Intend v a = mkVP v a ; Report v s = mkVP v s ;
    Give v a b = mkVP v a b ; Ask v n a = mkVP v n a ;
    Be a = mkVP a ; BeAt a = mkVP a ; Can v = mkVP can_VV v ;
    WithAdv v a = mkVP v a ;
    PP p n = SyntaxEng.mkAdv p n ;
}
