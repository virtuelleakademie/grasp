first_message = (
    "Ich helfe dir heute das Prinzip der Varianzanalyse (ANOVA) zu verstehen, "
    "wie und wofür es eingesetzt wird.\n"
    "Ziel der ANOVA ist es, herauszufinden, ob sich eine bestimmte Beobachtungsgrösse "
    "zwischen verschiedenen Gruppen wesentlich unterscheidet."
)

main_question = {
    1 : (
        "Dieses Bild zeigt die Konzentrationswerte in Abhängigkeit von vorherigem Koffeinkonsum. "
        "Klicke einmal darauf, um die Details zu sehen. "
        "Diesen Daten nach zu urteilen: hat Koffein eine Auswirkung auf Konzentration? "
        "Ist diese Auswirkung signifikant?"
    ), ## start by giving the full data right away -> answer is no
    2 : (
        "Dieses Bild zeigt nun die Konzentrationswerte in Abhängigkeit von vorherigem Koffeinkonsum, "
        "unterteilt nach Müdigkeit. "
        "Diesen Daten nach zu urteilen: Welchen Effekt haben Koffeinkonsum und Müdigkeit auf die Konzentration? "
        "Wie unterscheidet sich deren Effekt? "
        "Sind die Auswirkungen signifikant?"
    )
}


main_answer = {
    1 : (
        "Beobachtungen:\n"
        "- der Mittelwert steigt mit Koffeinkonsum leicht an.\n"
        "- die Wurzel der Quadratsumme ist deutlich grösser als dieser Anstieg.\n"
        "- der resultierende F-Wert ist kleiner als der kritische Wert\n\n"
        "Schlussfolgerung:\n"
        "Mittelwert und mittlere Quadratsumme sind ein guter Hinweis, **der subkritische F-Wert lässt darauf schliessen, "
        "dass sich kein signifikanter Effekt von Koffein auf die Konzentration feststellen lässt.**"
    ),
    2: (
        "Beobachtungen:\n"
        "- Bei keiner Müdigkeit erhöht Koffein die Konzentration leicht. \n"
        "- Bei Müdigkeit hingegen wird diese durch Koffein gesenkt.\n"
        "- Müdigkeit senkt die Konzentration. Mit Koffein wird der Unterschied noch grösser.\n"
        "- Der Plot mit Müdigkeit auf der x-Achse zeigt gekreuzte Linien.\n"
        "- Die F-Wert sind wie folgt: Koffein unkritisch, Müdigkeit sehr kritisch, Interaktion und Gesamteffekt kritisch.\n\n"
        "Schlussfolgerung:\n"
        "**Müdigkeit hat einen deutlichen Haupteffekt, was durch den überkritischen F-Wert mit statistischer Signifikanz unterstützt wird. "
        "Koffein zeigt einen Interaktionseffekt mit Müdigkeit, deutlich an den gekreuzten Linien und dem kritischen F-Wert für die Interaktion zu sehen, "
        "und beeinflusst die Wirkung der Müdigkeit, obwohl Koffein keinen signifikanten Haupteffekt aufweist (erkennbar am subkritischen F-Wert für den Koffein-Haupteffekt)."
        "Insgesamt ist ein deutlicher Effekt auf die Konzentration zu sehen, "
        "der kritische F-Gesamtwert belegt statistische Signifikanz.**"
    ),
}

image = {
    1: {
        1 : "static/Question_1_Step_0.png",
        2 : "static/Question_1_Step_1.png",
        3 : None,
        4 : None,
        5 : "static/Question_1_Step_2.png",
        6 : "static/Question_1_Step_3.png",
    },
    2: {
        1 : "static/Question_2_Step_0.png",
        2 : "static/Question_2_Step_1.png",
        3 : "static/Question_2_Step_2.png",
        4 : "static/Question_2_Step_3.png",
    }
}


image_solution = {
    1 : "static/Question_1_summary.png",
    2 : None,
}


guiding_questions = {
    1 : {
        1: (
            "Wie kann ich in Zahlen feststellen, wie stark Koffeinkonsum die Konzentration im Mittel beeinflusst? "
        ),
        2: (
            "Wie stark ist die gesamte Abweichung der Messwerte vom Erwartungswert? "
            "Wie kann ich diese berechnen, ohne dass sich positive und negative Abweichungen aufheben?"
        ),
        3: "Wie viele unabhängige Informationen fliessen in die Quadratsummen ein?",
        4: "Wie gross ist die durchschnittliche Streuung der Daten?",
        5: "Wie stark unterscheidet sich die Streuung zwischen den Gruppen im Vergleich zur Streuung innerhalb der Gruppen?",
        6: "Basierend auf den Ergebnissen, ist der Einfluss von Koffein auf die Konzentration nun signifikant?",
    },
    2 : {
        1: "Für wieviele und welche Gruppen sollten nun der Mittelwert und MQS bestimmt werden, um eine bessere Übersicht zu erlauben?",
        2: "Wie unterscheidet sich der Einfluss von Müdigkeit und Koffein auf die Konzentration?",
        3: "Betrachten wir die Daten einmal anders. Bitte ordne zu, welcher Faktor einen Haupteffekt, welcher einen Interaktionseffekt hat?",
        4: (
            "Welche F-Werte müssen wir nun betrachten, um zu bestimmen, ob die Effekte der Faktoren, einzeln und gemeinsam, "
            "sowie deren Zusammenspiel signifikanten Einfluss auf die Konzentration haben?"
        ),
        5: "Wie sind diese Werte nun zu interpretieren?"
    }
        

}

guiding_answers = {
    1 : {
        1: (
            "Der Mittelwert einer Gruppen schätzt den Erwartungswert für Personen der Gruppe. "
            "Der Effekt der Gruppe ist definiert als die Abweichung ihres Mittelwerts vom Gesamtmittelwert. "
            "**Die Differenz zwischen den zwei Gruppenmittelwerten ist der Haupteffekt**, der die Differenz ihrer Effekte quantifiziert. "
        ),
        2: (
            "**Die Quadratsumme einer Gruppe zeigt die gesamte quadratische Abweichung vom Mittelwert.** "
            "Das Quadrat stellt sicher, dass alle Abweichung positiv addiert werden."
        ),
        3: (
            "**Der Freiheitsgrad gibt die Anzahl der unabhängigen Werte an, die zur Berechnung einer Statistik beitragen können.** "
            r"Jeder der $N$ Datenpunkte steht für eine unabhängige Messung. "
            "Wenn wir jedoch den Mittelwert berechnen, verlieren wir einen Freiheitsgrad, "
            "da der letzte Datenpunkt durch die anderen Werte und den Mittelwert festgelegt ist. "
            "Anders ausgedrückt: Wenn wir N-1 Werte und den Mittelwert kennen, ist der N-te Wert nicht mehr frei wählbar. Daher ist der Freiheitsgrad hier N-1."
        ),
        4: (
            "Die Quadratsumme gibt die gesamte Abweichung an. "
            "Der Freiheitsgrad die unabhängigen Parameter. "
            "Weil der Mittelwert aus den Daten geschätzt wird, ist er näher an den Daten als der wahre Mittelwert, "
            "was die Streuung künstlich kleiner erscheinen lässt. "
            r"Die Quadratsumme durch die Anzahl Datenpunkte n zu teilen würde die Streuung unterschätzen. "
            "Um diesen Schätzfehler zu korrigieren, teilt man die Quadratsumme (QS) stattdessen durch den Freiheitsgrad, um die Mittlere Quadratsumme zu berechnen. "
            "**Die Wurzel der mittleren Quadratsumme innerhalb der Gruppen (MQS) schätzt die Standardabweichung der Werte innerhalb der Gruppen---also wie stark einzelne Beobachtungen im Durchschnitt vom jeweiligen Gruppenmittelwert abweichen.**"
        ),
        5: (
            "**Der F-Wert** ist das Verhältnis von mittlerer Quadratsumme (MQS) zwischen den Gruppen und innerhalb der Gruppen. "
            "Er **misst also, ob der Unterschied zwischen den Gruppen grösser ist als die Unterschiede innerhalb der Gruppen.** "
            "Unter der Nullhypothese (dass es keinen Effekt gibt) erwarten wir einen F-Wert nahe 1. "
            "Der Wert wird interpretiert, indem er mit einem kritischen Wert verglichen wird, "
            "ab dem wir bei den gegebenen Freiheitsgraden und einem festgelegten Signifikanzniveau (z.B. $\\alpha=0.05$) "
            "mit statistischer Sicherheit annehmen können, dass sich die Gruppen tatsächlich voneinander unterscheiden."
        ),
        6: "**Wenn der F-Wert grösser ist als der kritische, dann ist der Einfluss signifikant."
    },
    2 : {
        1: (
            "Da nun zwei Einflussgrössen betrachtet werden, Koffein Ja/Nein und Müdigkeit Ja/Nein, "
            "erhalten wir **vier verschiedene Gruppen - (Ja,Ja), (Ja,Nein), (Nein,Ja) und (Nein,Nein)** - "
            "für die jeweils Mittelwert und Mittlere Quadratsumme (MQS) berechnet werden."
        ),
        2: "**Müdigkeit senkt stets die Konzentration**, wohingegen der **Effekt von Koffein unterschiedlich ist, je nach Müdigkeit**.",
        3: (
            "**Müdigkeit zeigt einen deutlichen Haupteffekt. Zwischen Müdigkeit und Koffein besteht ein signifikanter Interaktionseffekt**"
            "was bedeutet, dass der Effekt von Koffein von der Müdigkeit abhängt und umgekehrt.",
        ),
        4: (
            "Jeder Effekt muss separat betrachtet werden. **Es werden daher vier F-Werte benötigt: "
            "einer für Koffein, einer für Müdigkeit, einer für die Interaktion und einer für den Gesamteffekt.**"
        ),
        5: (
            "Die F-Werte zeigen das Verhältnis der Abweichung der Mittelwerte zueinander im Vergleich zur Abweichung der Daten von den jeweiligen Mittelwerten. "
            "Wenn ein oder mehrere Faktoren die Abweichung der Daten erklären können, durch entsprechendes Verändern des Mittelwertes, ist der Einfluss signifikant. "
            "Das zeigt sich dadurch, dass der **F-Wert über dem kritischen Wert liegt**, wobei dieser vom Freiheitsgrad abhängt. "
            "Der Gesamteffekt kombiniert sowohl die Haupteffekte als auch die Interaktionseffekte und hat somit 3 Freiheitsgrade (einen für jeden Effekt) und muss mit einem anderen kritischen Wert verglichen werden. "
            "**Koffein hat einen subkritischen F-Wert, also keinen signifikanten Haupteffekt**, "
            "**Müdigkeit, die Interaktion zwischen Müdigkeit und Koffein, sowie der Gesamteffekt sind deutlich über dem kritischen Wert und haben somit signifikanten Einfluss**"
        ),
    }
}



end_message = (
    "Gute Arbeit! Du hast die Aufgabe beendet.\n"
    "Danke für deinen tollen Einsatz!"
)