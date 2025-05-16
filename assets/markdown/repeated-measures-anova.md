# Übung: Einfaktorielle Varianzanalyse mit Messwiederholung (Repeated Measures ANOVA)

Diese Übung behandelt die einfaktorielle ANOVA mit Messwiederholung anhand eines praxisnahen Beispiels zur Veränderung der **Arbeitszufriedenheit** über drei Zeitpunkte. Ziel ist es, die Konzepte zu verstehen und statistisch anzuwenden.

---

## Lernziele

- Verständnis des Designs mit abhängigen Stichproben
- Zerlegung der Gesamtvarianz in Bedingungs-, Personen- und Residualvarianz
- Durchführung eines Signifikanztests (F-Test)
- Berechnung und Interpretation von Effektgrößen
- Durchführung eines Kontrasttests zur Überprüfung spezifischer Hypothesen (z. B. quadratischer Trend)

---

## Datengrundlage

Die Arbeitszufriedenheit von **5 Personen** wurde zu drei Zeitpunkten erhoben:  
**Anfang**, **nach 3 Monaten**, **nach 6 Monaten**.

| Vpn | Anfang | 3 Monate | 6 Monate |
|-----|--------|----------|----------|
| 1   | 9      | 4        | 5        |
| 2   | 9      | 4        | 8        |
| 3   | 9      | 7        | 14       |
| 4   | 10     | 9        | 5        |
| 5   | 8      | 1        | 3        |

---

## Aufgabe 1: Hypothesen

**a)** Formuliere die **Nullhypothese (H₀)** und die **Alternativhypothese (H₁)**.

- H₀:  
- H₁:  

---

## Aufgabe 2: Berechnung der Quadratsummen

Berechne:

- QS_total
- QS_zwischen_Personen
- QS_zwischen_Bedingungen
- QS_Residual

Hinweis: Verwende die Mittelwerte je Person, Bedingung und insgesamt.

---

## Aufgabe 3: Freiheitsgrade und Mittlere Quadratsummen

Berechne:

- df_zwischen_Bedingungen
- df_Residual
- MQS_zwischen_Bedingungen
- MQS_Residual

---

## Aufgabe 4: F-Test

Berechne den F-Wert und prüfe, ob dieser signifikant ist auf dem Niveau von α = 0.05.

- **F = MQS_zwischen_Bedingungen / MQS_Residual**

Vergleiche mit dem kritischen F-Wert bei df1 = 2 und df2 = 8.

---

## Aufgabe 5: Effektgrößen

Berechne:

- **Nicht-partieller Determinationskoeffizient (η²):**  
  \( \eta^2 = \frac{QS_{zwA}}{QS_{tot}} \)

- **Partieller Determinationskoeffizient (η²_p):**  
  \( \eta^2_p = \frac{QS_{zwA}}{QS_{zwA} + QS_{Res}} \)

---

## Aufgabe 6: Kontrastanalyse

**a)** Führe eine Kontrastanalyse mit einem **quadratischen Kontrast** (1, -2, 1) durch.

**b)** Berechne die Kontrastvariable pro Person und den zugehörigen t-Wert.

**c)** Beurteile die Signifikanz des Trends bei α = 0.05.

---

## Aufgabe 7: Interpretation

- Welche Bedingung hat den höchsten und welche den tiefsten Mittelwert?
- Wie würdest du die Ergebnisse interpretieren im Hinblick auf einen „Honeymoon“ oder „Hangover“-Effekt bei Arbeitszufriedenheit?
- Was bedeutet ein signifikanter quadratischer Trend?

---

## Bonus: Umsetzung in R

Nutze das Skript `Uebung_12_RMANOVA_Loesung.R`, um die ANOVA in **R** durchzuführen:

```r
library(afex)
data <- data.frame(
  id = factor(rep(1:5, each=3)),
  zeit = factor(rep(c("Anfang", "Monate3", "Monate6"), times=5)),
  zufriedenheit = c(9,4,5,9,4,8,9,7,14,10,9,5,8,1,3)
)
model <- aov_ez(id = "id", dv = "zufriedenheit", within = "zeit", data = data)
summary(model)
```

---

## Quellen

- Mayer, B. (2025). Übungen zu Statistik II. FS 2025. Universität Bern.  
- Eid et al. (2020). Statistik und Forschungsmethoden.  
- Budischewski & Günther (2020). Aufgabenbuch Statistik.

