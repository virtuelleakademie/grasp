#### Dr. Boris Mayer: Übungen zu Statistik II (Institut für Psychologie, Universität Bern)
#### Übung 12: Einfaktorielle Varianzanalyse mit Messwiederholung (RM-ANOVA) in R

### Packages laden

library(afex)
library(emmeans)
library(tidyverse) # für Datendefinition


### 1. Daten

honeymoon1 <- tibble(ID = as.factor(rep(1:5, times = 3)),
                     zufriedenheit = c(9, 9,  9, 10, 8,
                                       4, 4,  7,  9, 1,
                                       5, 8, 14,  5, 3),
                     zeit = as.factor(rep(c("Anfang",
                                            "Drei_Monate",
                                            "Sechs_Monate"), each = 5)))


honeymoon1 # Daten anschauen


### 2. Einfaktorielle ANOVA mit Messwiederholung

anova1MW <- aov_4(zufriedenheit ~ 1 + (zeit | ID), data = honeymoon1)


summary(anova1MW)
# Fun fact: QS_zwP als Error-SS des Intercepts im summary-Output enthalten

anova1MW$anova_table
# Hier werden standardmässig (unabhängig vom Ergebnis des Mauchly-Tests und von
# der Grösse von e_GG) die Greenhouse-Geisser-korrigierten F-Tests berichtet
# + Effektstärke ges (nicht-partielles eta^2)


# Plot der Mittelwerte
# Für den Plot verwenden wir die Funktion `afex_plot(object, x)` aus dem `afex`-Package.
# Als erstes Argument der Funktion wird das Ergebnisobjekt der ANOVA benötigt.
# Für das Argument `x =` muss die Gruppierungsvariable/Faktor angegeben werden.
# Mit `error = "within"` erhält man die für messwiederholte Daten angepassten
# Standardfehler/Konfidenzintervalle.
# Im Plot werden per default Mittelwerte mit den 95 %-Konfidenzintervallen pro
# Stufe der unabhängigen Variable angezeigt. Mit error_ci = FALSE erhält man
# stattdessen die Standardfehler der Mittelwerte.

# `afex_plot()` erstellt ein ggplot-Objekt, welches wir weiter verändern können.
p <- afex_plot(object = anova1MW,
               x = "zeit",
               error = "within",
               error_ci = FALSE)

## Verschönern Sie den Plot, indem Sie folgende Elemente hinzufügen:
p +
    theme_classic() +                                                  # Hintergrund weiss
    ggtitle("Arbeitszufriedenheit im Verlauf") +                       # Titel hinzufügen
    xlab("Zeit") +                                                     # x-Achse beschriften
    ylab("Zufriedenheit")                                              # y-Achse beschriften




### 3. Post-hoc-Einzelvergleiche

# Die Funktion `emmeans(object, specs)` benötigt für die Berechnung der Post-hoc-Einzelvergleiche
# als erstes Argument die Ergebnis-Tabelle der ANOVA. Als zweites Argument muss
# die Gruppierungsvariable/Faktor mit einer Tilde `~` angegeben werden.
# Wir speichern das Ergebnis unter `result1MW` ab, um damit weiterrechnen zu können.
result1MW <- emmeans(object = anova1MW, specs = ~ zeit)

# ALLE möglichen Post-hoc-Einzelvergleiche erhalten wir, indem wir die Funktion
# `pairs(x, adjust)` auf das Ergebnisobjekt (x) der `emmeans()`-Funktion anwenden.
# Mit dem Argument `adjust` wird dabei die Korrekturmethode bestimmt.
# Hier lassen wir uns zunächst die unkorrigierten p-Werte ausgeben (adjust = "none")
# und anschliessend die nach Tukey korrigierten (auch mit Pipe möglich):
result1MW |> pairs(adjust = "none")
result1MW |> pairs(adjust = "tukey")
# mit der Tukey-Korrektur ist der erste Vergleich (Anfang - Drei_Monate) signifikant, aber:
# Post-hoc Einzelvergleiche hier nur zur Veranschaulichung, da der Omnibustest der
# Varianzanalyse mit Messwiederholung nicht signifikant war.



### 4. Polynomiale Trendkontraste

# Trendkontraste lassen sich mit der emmeans-Funktion `contrast()` zusammen mit dem
# oben definierten emmeans-Objekt und mit dem Argument `method = "poly"` berechnen.
# Es werden immer alle möglichen Trendkontraste ausgegeben (hier: linear und quadratisch).
# Da wir uns hier aus theoretischen Gründen nur für den quadratischen Kontrast
# interessieren, ist eine Alpha-Korrektur nicht notwendig (`adjust = "none"`)
contrast(object = result1MW, method = "poly", adjust = "none")
# Alternativ mit Pipe:
result1MW |> contrast(method = "poly", adjust = "none")
# Da wir die gerichtete Alternativhypothese eines POSITIVEN quadratischen Trends
# testen (U-förmiger Verlauf der Arbeitszufriedenheit), muss der p-Wert des
# quadratischen Kontrasts noch halbiert werden! -> p = 0.0306 -> sig.


# Kontrastkoeffizienten verifizieren mit coef():
coef(contrast(object = result1MW, method = "poly"))



### 5. Vertiefung: Einfaktorielle ANOVA mit Messwiederholung in R Schritt für Schritt

# Hier wird gezeigt, wie man die ANOVA in R mit `mutate()` und `summarize()` parallel
# zu den von Hand vorgenommenen Berechnungen durchführen kann.
table <- honeymoon1 |>
    mutate(mean = mean(zufriedenheit)) |>            # Gesamtmittelwert
    group_by(zeit) |>
    mutate(mean_bedingung = mean(zufriedenheit)) |>  # Bedingungsmittelwerte A
    group_by(ID) |>
    mutate(mean_person = mean(zufriedenheit)) |>     # Personenmittelwerte
    ungroup() |>
    summarize(QS_tot = sum((zufriedenheit - mean)^2),
              QS_zwA = sum((mean_bedingung - mean)^2),
              QS_zwP = sum((mean_person - mean)^2),
              QS_Res = QS_tot - QS_zwA - QS_zwP,
              J = length(levels(zeit)),
              n = length(levels(ID)),
              df_zwA = J - 1,
              df_Res = (n - 1) * (J - 1),
              MQS_zwA = QS_zwA / df_zwA,
              MQS_Res = QS_Res / df_Res,
              F_zwA = MQS_zwA / MQS_Res,
              F_Res = NA,                  # für Umformung in Tabelle
              p_zwA = pf(F_zwA, df_zwA, df_Res, lower.tail = FALSE),
              p_Res = NA,                  # für Umformung in Tabelle
              etasq_zwA = QS_zwA / QS_tot,
              etasqp_zwA = QS_zwA / (QS_zwA + QS_Res),
              etasq_Res = NA,              # für Umformung in Tabelle
              etasqp_Res = NA) |>          # für Umformung in Tabelle
    select(-QS_tot, -QS_zwP, -n, -J)       # werden für Tabelle nicht benötigt


table |> pivot_longer(everything(),
                         names_to = c(".value", "source"),
                         names_sep = "_")
