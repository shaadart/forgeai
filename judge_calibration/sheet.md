# Judge hand check

Write `pass` or `fail` after each `Label:`. Do not open judge_verdicts.json first.

**pass** needs both: every statement in the answer is backed by the evidence, and
for `answer` all key facts are there; for `refuse` the reply declines;
for `clarify` it asks which one is meant, or covers the key facts.

## 1. mlc-crew-rights/T12 (expected: answer)

**Question:** What is the minimum annual leave entitlement for seafarers according to the Maritime Labour Convention, 2006?

**Key facts:** The minimum annual leave with pay entitlement is 2.5 calendar days per month of employment.

**Reply (answered):** 2.5 calendar days per month of employment

**Evidence:**

> 34 Maritime Labour Convention, 2006 Standard A2.4 – Entitlement to leave 1. Each Member shall adopt laws and regulations determining the minimum standards for annual leave for seafarers serving on ships that fly its flag, taking proper account of the special needs of seafarers with respect to such leave. 2. Subject to any collective agreement or laws or regulations providing for an appropriate method of calculation that takes account of the special needs of seafarers in this respect, the annual leave with pay entitlement shall be calculated on the basis of a minimum of 2.5 calendar days per month of employment. The manner in which the length of service is calculated shall be determined by the competent authority or through the appropriate machinery in each country. Justified absences from work shall not be considered as annual leave. 3. Any agreement to forgo the minimum annual leave with pay prescribed in this Standard, except in cases provided for by the competent authority, shall be prohibited.

> Standard A2.3, paragraph 14. Regulation 2.4 – Entitlement to leave Purpose: To ensure that seafarers have adequate leave 1. Each Member shall require that seafarers employed on ships that fly its flag are given paid annual leave under appropriate conditions, in accordance with the provisions in the Code. 2. Seafarers shall be granted shore leave to benefit their health and well-being and consistent with the operational requirements of their positions.

> Guideline B2.4 – Entitlement to leave Guideline B2.4.1 – Calculation of entitlement 1. Under conditions as determined by the competent authority or through the appropriate machinery in each country, service off-articles should be counted as part of the period of service. 2. Under conditions as determined by the competent authority or in an applicable collective agreement, absence from work to attend an approved maritime vocational training course or for such reasons as illness or injury or for maternity should be counted as part of the period of service. 3. The level of pay during annual leave should be at the seafarer’s normal level of remuneration provided for by national laws or regulations or in the applicable seafarers’ employment agreement. For seafarers employed for periods shorter than one year or in the event of termination of the employment relationship, entitlement to leave should be calculated on a pro-rata basis. 4. The following should not be counted as part of annual leave with pay: (a) public and customary holidays recognized as such in the flag State, whether or not they fall during the annual leave with pay; (b) periods of incapacity for work resulting from illness or injury or from maternity, under conditions as determined by the competent authority or through the appropriate machinery in each country; (c) temporary shore leave granted to a seafarer while under an employment agreement; and (d) compensatory leave of any kind, under conditions as determined by the competent authority or through the appropriate machinery in each country.

> 35 Conditions of employment 2. Seafarers should in principle have the right to take annual leave in the place with which they have a substantial connection, which would normally be the same as the place to which they are entitled to be repatriated. Seafarers should not be required without their consent to take annual leave due to them in another place except under the provisions of a seafarers’ employment agreement or of national laws or regulations. 3. If seafarers are required to take their annual leave from a place other than that permitted by paragraph 2 of this Guideline, they should be entitled to free transportation to the place where they were engaged or recruited, whichever is nearer their home; subsistence and other costs directly involved should be for the account of the shipowner; the travel time involved should not be deducted from the annual leave with pay due to the seafarer. 4. A seafarer taking annual leave should be recalled only in cases of extreme emergency and with the seafarer’s consent.

> 26 Maritime Labour Convention, 2006 bargaining agreement is not in English, the following shall also be available in English (except for ships engaged only in domestic voyages): (a) a copy of a standard form of the agreement; and (b) the portions of the collective bargaining agreement that are subject to a port State inspection under Regulation 5.2. 3. The document referred to in paragraph 1(e) of this Standard shall not contain any statement as to the quality of the seafarers’ work or as to their wages. The form of the document, the particulars to be recorded and the manner in which such particulars are to be entered, shall be determined by national law. 4. Each Member shall adopt laws and regulations specifying the matters that are to be included in all seafarers’ employment agreements governed by its national law. Seafarers’ employment agreements shall in all cases contain the following particulars: (a) the seafarer’s full name, date of birth or age, and birthplace; (b) the shipowner’s name and address; (c) the place where and date when the seafarers’ employment agreement is entered into; (d) the capacity in which the seafarer is to be employed; (e) the amount of the seafarer’s wages or, where applicable, the formula used for calculating them; (f) the amount of paid annual leave or, where applicable, the formula used for calculating it; (g) the termination of the agreement and the conditions thereof, including: (i) if the agreement has been made for an indefinite period, the conditions entitling either party to terminate it, as well as the required notice period, which shall not be less for the shipowner than for the seafarer; (ii) if the agreement has been made for a definite period, the date fixed for its expiry; and (iii) if the agreement has been made for a voyage, the port of destination and the time which has to expire after arrival before the seafarer should be discharged; (h) the health and social security protection benefits to be provided to the seafarer by the shipowner; (i) the seafarer’s entitlement to repatriation; (j) reference to the collective bargaining agreement, if applicable; and (k) any other particulars which national law may require. 5. Each Member shall adopt laws or regulations establishing minimum notice

Label: 

## 2. spares-procurement/T06 (expected: refuse)

**Question:** Could you tell me the next port of call for the ballast pump BP-200?

**Key facts:** none

**Reply (refused):** I can't find that in the catalogue or supplier terms. Try rephrasing, or ask your manager or the responsible department.

**Evidence:**

> part_no: G-BP200-090-AM; description: Pump shaft, aftermarket; equipment: ballast pump BP-200; supplier: Gulfstream Pumpworks; unit_price: 497.51; currency: USD; lead_time_days: 8; moq: 1; in_stock: yes

> part_no: G-BP200-040-AM; description: Shaft sleeve, aftermarket; equipment: ballast pump BP-200; supplier: Gulfstream Pumpworks; unit_price: 569.51; currency: USD; lead_time_days: 12; moq: 1; in_stock: no

> part_no: N-BP200-090-AM; description: Pump shaft, aftermarket; equipment: ballast pump BP-200; supplier: Nordsee Marine Spares; unit_price: 416.05; currency: EUR; lead_time_days: 4; moq: 1; in_stock: no

> part_no: G-BP200-090-OE; description: Pump shaft, OEM; equipment: ballast pump BP-200; supplier: Gulfstream Pumpworks; unit_price: 586.93; currency: USD; lead_time_days: 18; moq: 1; in_stock: yes

> part_no: G-BP200-050-AM; description: Ball bearing, aftermarket; equipment: ballast pump BP-200; supplier: Gulfstream Pumpworks; unit_price: 513.29; currency: USD; lead_time_days: 4; moq: 4; in_stock: yes

Label: 

## 3. mlc-crew-rights/S07 (expected: answer)

**Question:** What should shipowners do regarding the costs of repatriation until seafarers are landed or provided with suitable employment?

**Key facts:** Shipowners should continue to cover the costs of repatriation.

**Reply (answered):** Shipowners should be required to continue to cover the costs of repatriation until the seafarers concerned are landed at a destination prescribed pursuant to this Code or are provided with suitable employment on board a ship proceeding to one of those destinations.

**Evidence:**

> to the repatriation destination. 4. Time spent awaiting repatriation and repatriation travel time should not be deducted from paid leave accrued to the seafarers. 5. Shipowners should be required to continue to cover the costs of repatriation until the seafarers concerned are landed at a destination prescribed pursuant to this Code or are provided with suitable employment on board a ship proceeding to one of those destinations. 6. Each Member should require that shipowners take responsibility for repatriation arrangements by appropriate and expeditious means. The normal mode of transport should be by air. The Member should prescribe the destinations to which seafarers may be repatriated. The destinations should include the countries with which seafarers may be deemed to have a substantial connection including: (a) the place at which the seafarer agreed to enter into the engagement;

> the State of which they are a national may arrange for their repatriation and recover the cost from the Member whose flag the ship flies; (b) costs incurred in repatriating seafarers shall be recoverable from the shipowner by the Member whose flag the ship flies; (c) the expenses of repatriation shall in no case be a charge upon the seafarers, except as provided for in paragraph 3 of this Standard. 6. Taking into account applicable international instruments, including the International Convention on Arrest of Ships, 1999, a Member which has paid the cost of repatriation pursuant to this Code may detain, or request the detention of, the ships of the shipowner concerned until the reimbursement has been made in accordance with paragraph 5 of this Standard. 7. Each Member shall facilitate the repatriation of seafarers serving on ships which call at its ports or pass through its territorial or internal waters, as well as their replacement on board.

> 38 Maritime Labour Convention, 2006 8. Assistance provided by the financial security system shall be granted promptly upon request made by the seafarer or the seafarer’s nominated representative and supported by the necessary justification of entitlement in accordance with paragraph 2 above. 9. Having regard to Regulations 2.2 and 2.5, assistance provided by the financial security system shall be sufficient to cover the following: (a) outstanding wages and other entitlements due from the shipowner to the seafarer under their employment agreement, the relevant collective bargaining agreement or the national law of the flag State, limited to four months of any such outstanding wages and four months of any such outstanding entitlements; (b) all expenses reasonably incurred by the seafarer, including the cost of repatriation referred to in paragraph 10; and (c) the essential needs of the seafarer including such items as: adequate food, clothing where necessary, accommodation, drinking water supplies, essential fuel for survival on board the ship, necessary medical care and any other reasonable costs or charges from the act or omission constituting the abandonment until the seafarer’s arrival at home. 10. The cost of repatriation shall cover travel by appropriate and expeditious means, normally by air, and include provision for food and accommodation of the seafarer from the time of leaving the ship until arrival at the seafarer’s home, necessary medical care, passage and transport of personal effects and any other reasonable costs or charges arising from the abandonment. 11. The financial security shall not cease before the end of the period of validity of the financial security unless the financial security provider has given prior notification of at least 30 days to the competent authority of the flag State. 12. If the provider of insurance or other financial security has made any payment to any seafarer in accordance with this Standard, such provider shall, up to the amount it has paid and in accordance with the applicable law, acquire by subrogation, assignment or otherwise, the rights which the seafarer would have enjoyed. 13. Nothing in this Standard shall prejudice any right of recourse of the insurer or provider of financial security against third parties.

> 36 Maritime Labour Convention, 2006 (a) if the seafarers’ employment agreement expires while they are abroad; (b) when the seafarers’ employment agreement is terminated: (i) by the shipowner; or (ii) by the seafarer for justified reasons; and also (c) when the seafarers are no longer able to carry out their duties under their employment agreement or cannot be expected to carry them out in the specific circumstances. 2. Each Member shall ensure that there are appropriate provisions in its laws and regulations or other measures or in collective bargaining agreements, prescribing: (a) the circumstances in which seafarers are entitled to repatriation in accordance with paragraph 1(b) and (c) of this Standard; (b) the maximum duration of service periods on board following which a seafarer is entitled to repatriation – such periods to be less than 12 months; and (c) the precise entitlements to be accorded by shipowners for repatriation, including those relating to the destinations of repatriation, the mode of transport, the items of expense to be covered and other arrangements to be made by shipowners. 3. Each Member shall prohibit shipowners from requiring that seafarers make an advance payment towards the cost of repatriation at the beginning of their employment, and also from recovering the cost of repatriation from the seafarers’ wages or other entitlements except where the seafarer has been found, in accordance with national laws or regulations or other measures or applicable collective bargaining agreements, to be in serious default of the seafarer’s employment obligations. 4. National laws and regulations shall not prejudice any right of the shipowner to recover the cost of repatriation under third-party contractual arrangements. 5. If a shipowner fails to make arrangements for or to meet the cost of repatriation of seafarers who are entitled to be repatriated: (a) the competent authority of the Member whose flag the ship flies shall arrange for repatriation of the seafarers concerned; if it fails to do so, the State from which the seafarers are to be repatriated or the State of which they are a national may arrange for their repatriation and recover the cost from the Member whose flag the ship flies; (b) costs incurred in repatriating seafarers shall be recoverable from the shipowner

> 37 Conditions of employment 8. In particular, a Member shall not refuse the right of repatriation to any seafarer because of the financial circumstances of a shipowner or because of the shipowner’s inability or unwillingness to replace a seafarer. 9. Members shall facilitate the prompt repatriation of seafarers, including when they are deemed abandoned within the meaning of Standard A2.5.2, paragraph 2. Port States, flag States and labour-supplying States shall cooperate to ensure that seafarers engaged on a ship to replace seafarers who have been abandoned in their territory, or on a ship flying their flag, shall be accorded their rights and entitlements under this Convention. 10. Each Member shall require that ships that fly its flag carry and make available to seafarers a copy of the applicable national provisions regarding repatriation written in an appropriate language.

Label: 

## 4. mlc-crew-rights/S04 (expected: clarify)

**Question:** What are the main obligations of the competent authority regarding seafarer recruitment and placement services?

**Key facts:** The competent authority should consider promoting effective cooperation among seafarer recruitment and placement services.; Consideration should be given to encouraging international cooperation between Members and relevant organizations.

**Reply (answered):** The competent authority shall closely supervise and control all seafarer recruitment and placement services operating in the territory of the Member concerned. Any licences or certificates or similar authorizations for the operation of private services in the territory are granted or renewed only after verification that the seafarer recruitment and placement service concerned meets the requirements of national laws and regulations. (C2, iv, v, vi, 6)

**Evidence:**

> Standard A1.4 – Recruitment and placement 1. Each Member that operates a public seafarer recruitment and placement service shall ensure that the service is operated in an orderly manner that protects and promotes seafarers’ employment rights as provided in this Convention. 2. Where a Member has private seafarer recruitment and placement services operating in its territory whose primary purpose is the recruitment and placement of seafarers or which recruit and place a significant number of seafarers, they shall be operated only in conformity with a standardized system of licensing or certification or other form of regulation. This system shall be established, modified or changed only after consultation with the shipowners’ and seafarers’ organizations concerned. In the event of doubt as to whether this Convention applies to a private recruitment and placement service, the question shall be determined by the competent authority in each Member after consultation with the shipowners’ and seafarers’ organizations concerned. Undue proliferation of private seafarer recruitment and placement services shall not be encouraged. 3. The provisions of paragraph 2 of this Standard shall also apply – to the extent that they are determined by the competent authority, in consultation with the shipowners’ and seafarers’ organizations concerned, to be appropriate – in the context of recruitment and placement services operated by a seafarers’ organization in the territory of the Member for the supply of seafarers who are nationals of that Member to ships which fly its flag. The services covered by this paragraph are those fulfilling the following conditions: (a) the recruitment and placement service is operated pursuant to a collective bargaining agreement between that organization and a shipowner; (b) both the seafarers’ organization and the shipowner are based in the territory of the Member; (c) the Member has national laws or regulations or a procedure to authorize or register the collective bargaining agreement permitting the operation of the recruitment and placement service; and (d) the recruitment and placement service is operated in an orderly manner and measures are in place to protect and promote seafarers’ employment rights comparable to those provided in paragraph 5 of this Standard.

> employment agreements are in accordance with applicable laws and regulations and any collective bargaining agreement that forms part of the employment agreement; (iv) make sure, as far as practicable, that the shipowner has the means to protect seafarers from being stranded in a foreign port; (v) examine and respond to any complaint concerning their activities and advise the competent authority of any unresolved complaint; (vi) establish a system of protection, by way of insurance or an equivalent appropriate measure, to compensate seafarers for monetary loss that they may incur as a result of the failure of a recruitment and placement service or the relevant shipowner under the seafarers’ employment agreement to meet its obligations to them, and ensure that seafarers are informed, prior to or in the process of engagement, of their rights under that system. 6. The competent authority shall closely supervise and control all seafarer recruitment and placement services operating in the territory of the Member concerned. Any licences or certificates or similar authorizations for the operation of private services in the territory are granted or renewed only after verification that the seafarer recruitment and placement service concerned meets the requirements of national laws and regulations.

> Guideline B5.3 – Labour-supplying responsibilities 1. Private seafarer recruitment and placement services established in the Member’s territory and securing the services of a seafarer for a shipowner, wherever located, should be required to assume obligations to ensure the proper fulfilment by shipowners of the terms of their employment agreements concluded with seafarers.

> 23 Minimum requirements for seafarers to work on a ship ship’s safe navigation and pollution prevention operations have had adequate training, including approved sea-service experience, and have relevant knowledge of the maritime industry, including the relevant maritime international instruments on training, certification and labour standards; (g) prescribing operational standards and adopting codes of conduct and ethical practices for seafarer recruitment and placement services; and (h) exercising supervision of the licensing or certification system on the basis of a system of quality standards. 2. In establishing the system referred to in Standard A1.4, paragraph 2, each Member should consider requiring seafarer recruitment and placement services, established in its territory, to develop and maintain verifiable operational practices. These operational practices for private seafarer recruitment and placement services and, to the extent that they are applicable, for public seafarer recruitment and placement services should address the following matters: (a) medical examinations, seafarers’ identity documents and such other items as may be required for the seafarer to gain employment; (b) maintaining, with due regard to the right to privacy and the need to protect confidentiality, full and complete records of the seafarers covered by their recruitment and placement system, which should include but not be limited to: (i) the seafarers’ qualifications; (ii) record of employment; (iii) personal data relevant to employment; and (iv) medical data relevant to employment; (c) maintaining up-to-date lists of the ships for which the seafarer recruitment and placement services provide seafarers and ensuring that there is a means by which the services can be contacted in an emergency at all hours; (d) procedures to ensure that seafarers are not subject to exploitation by the seafarer recruitment and placement services or their personnel with regard to the offer of engagement on particular ships or by particular companies; (e) procedures to prevent the opportunities for exploitation of seafarers arising from the issue of joining advances or any other financial transaction between the shipowner and the seafarers which are handled by the seafarer recruitment and placement services; (f) clearly publicizing costs, if any, which the seafarer will be expected to bear in the recruitment process; (g) ensuring that seafarers are advised of any particular conditions applicable to the

> the seafarer recruitment and placement services; (f) clearly publicizing costs, if any, which the seafarer will be expected to bear in the recruitment process; (g) ensuring that seafarers are advised of any particular conditions applicable to the job for which they are to be engaged and of the particular shipowner’s policies relating to their employment; (h) procedures which are in accordance with the principles of natural justice for dealing with cases of incompetence or indiscipline consistent with national laws and practice and, where applicable, with collective agreements; (i) procedures to ensure, as far as practicable, that all mandatory certificates and documents submitted for employment are up to date and have not been fraudulently obtained and that employment references are verified;

Label: 

## 5. spares-procurement/T02 (expected: refuse)

**Question:** When will the parts be delivered?

**Key facts:** none

**Reply (refused):** I cannot help with delivery times or vessel port calls. Please refer to your manager or the responsible department for this information.

**Evidence:**

> 6. Returns Unused parts may be returned within 30 days with a 20 percent restocking fee.

> 5. Part grade Safety-critical parts for the main engine must be OEM grade. Aftermarket parts may be used for pumps with superintendent agreement. 6. Urgent orders Express handling needs approval from a technical superintendent. 7. Exceptions Send any question this policy does not cover to the purchasing manager.

> 3. Payment Invoices are payable within 30 days of the invoice date. 4. Lead time Catalogue lead times are calendar days counted from order confirmation. Orders received after 15:00 Central European Time are confirmed on the next working day. Delivery to the vessel adds 2 calendar days for port clearance.

> 3. Payment Invoices are payable within 45 days of the invoice date. 4. Lead time Catalogue lead times are calendar days counted from order confirmation. Orders received after 12:00 Central European Time are confirmed on the next working day. Delivery to the vessel adds 2 calendar days for port clearance.

> Fleet procurement policy Version 4, effective 1 April 2026. Synthetic demonstration document. 1. Scope This policy covers spare parts ordered for vessels in the fleet. 2. Quotations Compare at least two suppliers where two list the part. Orders with a goods value above 5,000 in the order currency need two written quotations.

Label: 

## 6. spares-procurement/T07 (expected: answer)

**Question:** What is the part number and unit price of the gland packing set for the CW-150 cooling water pump, and is it currently in stock?

**Key facts:** The part number is N-CW150-100-AM.; The unit price is 326.58 EUR.; The gland packing set is not in stock.

**Reply (answered):** The part number is G-CW150-100-OE, the unit price is 405.87 USD, and it is currently in stock.

**Evidence:**

> part_no: G-CW150-100-AM; description: Gland packing set, aftermarket; equipment: cooling water pump CW-150; supplier: Gulfstream Pumpworks; unit_price: 356.09; currency: USD; lead_time_days: 3; moq: 4; in_stock: no

> part_no: G-CW150-100-OE; description: Gland packing set, OEM; equipment: cooling water pump CW-150; supplier: Gulfstream Pumpworks; unit_price: 405.87; currency: USD; lead_time_days: 9; moq: 4; in_stock: yes

> part_no: N-CW150-100-AM; description: Gland packing set, aftermarket; equipment: cooling water pump CW-150; supplier: Nordsee Marine Spares; unit_price: 326.58; currency: EUR; lead_time_days: 5; moq: 4; in_stock: no

> part_no: N-CW150-100-OE; description: Gland packing set, OEM; equipment: cooling water pump CW-150; supplier: Nordsee Marine Spares; unit_price: 450.36; currency: EUR; lead_time_days: 11; moq: 4; in_stock: no

> part_no: G-CW150-090-AM; description: Pump shaft, aftermarket; equipment: cooling water pump CW-150; supplier: Gulfstream Pumpworks; unit_price: 168.26; currency: USD; lead_time_days: 11; moq: 1; in_stock: yes

Label: 

## 7. mlc-crew-rights/T01 (expected: answer)

**Question:** What condition must be met for a seafarer to be entitled to repatriation according to the guideline?

**Key facts:** Seafarers should be entitled to repatriation upon the expiry of the period of notice given in accordance with the provisions of the seafarers’ employment agreement.

**Reply (answered):** The seafarer must be entitled to repatriation in the case covered by Standard A2.5, paragraph 1(a), upon the expiry of the period of notice given in accordance with the provisions of the seafarers’ employment agreement. Additionally, the seafarer must meet one of the following conditions: (i) in the event of illness or injury or other medical condition which requires their repatriation when found medically fit to travel; (ii) in the event of shipwreck; (iii) in the event of the shipowner not being able to continue to fulfil their legal or contractual obligations as an employer of the seafarers by reason of insolvency, sale of ship, change of ship’s registration or any other similar reason; (iv) in the event of a ship being bound for a war zone, as defined by national laws or regulations or seafarers’ employment agreements, to which the seafarer does not consent to go; and (v) in the event of termination or interruption of employment in accordance with an industrial award or collective agreement, or termination of employment for any other similar reason. [C1] (file: mlc_2006_consolidated_2022.pdf) "Seafarers should be entitled to repatriation: (a) in the case covered by Standard A2.5, paragraph 1(a), upon the expiry of the period of notice given in accordance with the provisions of the seafarers’ employment agreement;" [C3] (file: mlc_2006_consolidated_2022.pdf) "(i) in the event of illness or injury or other medical condition which requires their repatriation when found medically fit to travel; (ii) in the event of shipwreck; (iii) in the event of the shipowner not being able to continue to fulfil their legal or contractual obligations as an employer of the seafarers by reason of insolvency, sale of ship, change of ship’s registration or any other similar reason; (iv) in the event of a ship being bound for a war zone, as defined by national laws or regulations or seafarers’ employment agreements, to which the seafarer does not consent to go; and (v) in the event of termination or interruption of employment in accordance with an industrial award or collective agreement, or termination of employment for any other similar reason."

**Evidence:**

> Guideline B2.5 – Repatriation Guideline B2.5.1 – Entitlement 1. Seafarers should be entitled to repatriation: (a) in the case covered by Standard A2.5, paragraph 1(a), upon the expiry of the period of notice given in accordance with the provisions of the seafarers’ employment agreement;

> Standard A2.5.1 – Repatriation 1. Each Member shall ensure that seafarers on ships that fly its flag are entitled to repatriation in the following circumstances:

> 39 Conditions of employment (b) in the cases covered by Standard A2.5, paragraph 1(b) and (c): (i) in the event of illness or injury or other medical condition which requires their repatriation when found medically fit to travel; (ii) in the event of shipwreck; (iii) in the event of the shipowner not being able to continue to fulfil their legal or contractual obligations as an employer of the seafarers by reason of insolvency, sale of ship, change of ship’s registration or any other similar reason; (iv) in the event of a ship being bound for a war zone, as defined by national laws or regulations or seafarers’ employment agreements, to which the seafarer does not consent to go; and (v) in the event of termination or interruption of employment in accordance with an industrial award or collective agreement, or termination of employment for any other similar reason. 2. In determining the maximum duration of service periods on board following which a seafarer is entitled to repatriation, in accordance with this Code, account should be taken of factors affecting the seafarers’ working environment. Each Member should seek, wherever possible, to reduce these periods in the light of technological changes and developments and might be guided by any recommendations made on the matter by the Joint Maritime Commission. 3. The costs to be borne by the shipowner for repatriation under Standard A2.5 should include at least the following: (a) passage to the destination selected for repatriation in accordance with paragraph 6 of this Guideline; (b) accommodation and food from the moment the seafarers leave the ship until they reach the repatriation destination; (c) pay and allowances from the moment the seafarers leave the ship until they reach the repatriation destination, if provided for by national laws or regulations or collective agreements; (d) transportation of 30 kg of the seafarers’ personal luggage to the repatriation destination; and (e) medical treatment when necessary until the seafarers are medically fit to travel to the repatriation destination. 4. Time spent awaiting repatriation and repatriation travel time should not be deducted from paid leave accrued to the seafarers. 5. Shipowners should be required to continue to cover the costs of repatriation

> 36 Maritime Labour Convention, 2006 (a) if the seafarers’ employment agreement expires while they are abroad; (b) when the seafarers’ employment agreement is terminated: (i) by the shipowner; or (ii) by the seafarer for justified reasons; and also (c) when the seafarers are no longer able to carry out their duties under their employment agreement or cannot be expected to carry them out in the specific circumstances. 2. Each Member shall ensure that there are appropriate provisions in its laws and regulations or other measures or in collective bargaining agreements, prescribing: (a) the circumstances in which seafarers are entitled to repatriation in accordance with paragraph 1(b) and (c) of this Standard; (b) the maximum duration of service periods on board following which a seafarer is entitled to repatriation – such periods to be less than 12 months; and (c) the precise entitlements to be accorded by shipowners for repatriation, including those relating to the destinations of repatriation, the mode of transport, the items of expense to be covered and other arrangements to be made by shipowners. 3. Each Member shall prohibit shipowners from requiring that seafarers make an advance payment towards the cost of repatriation at the beginning of their employment, and also from recovering the cost of repatriation from the seafarers’ wages or other entitlements except where the seafarer has been found, in accordance with national laws or regulations or other measures or applicable collective bargaining agreements, to be in serious default of the seafarer’s employment obligations. 4. National laws and regulations shall not prejudice any right of the shipowner to recover the cost of repatriation under third-party contractual arrangements. 5. If a shipowner fails to make arrangements for or to meet the cost of repatriation of seafarers who are entitled to be repatriated: (a) the competent authority of the Member whose flag the ship flies shall arrange for repatriation of the seafarers concerned; if it fails to do so, the State from which the seafarers are to be repatriated or the State of which they are a national may arrange for their repatriation and recover the cost from the Member whose flag the ship flies; (b) costs incurred in repatriating seafarers shall be recoverable from the shipowner

> 37 Conditions of employment 8. In particular, a Member shall not refuse the right of repatriation to any seafarer because of the financial circumstances of a shipowner or because of the shipowner’s inability or unwillingness to replace a seafarer. 9. Members shall facilitate the prompt repatriation of seafarers, including when they are deemed abandoned within the meaning of Standard A2.5.2, paragraph 2. Port States, flag States and labour-supplying States shall cooperate to ensure that seafarers engaged on a ship to replace seafarers who have been abandoned in their territory, or on a ship flying their flag, shall be accorded their rights and entitlements under this Convention. 10. Each Member shall require that ships that fly its flag carry and make available to seafarers a copy of the applicable national provisions regarding repatriation written in an appropriate language.

Label: 

## 8. spares-procurement/T15 (expected: answer)

**Question:** How long is the lead time for the mechanical seal and what is the minimum order quantity?

**Key facts:** The lead time is 18 days.; The minimum order quantity is 1 unit.

**Reply (answered):** The lead time for the mechanical seal is 30 calendar days from order confirmation, plus 2 calendar days for port clearance. The minimum order quantity is not specified in the provided context, but it is mentioned that smaller orders are not accepted by Nordsee Marine Spares, which implies a minimum order quantity of 1 unit. However, this information is not explicitly stated in the context. 

**Evidence:**

> 3. Payment Payment is due within 30 days of shipment. 4. Lead time Catalogue lead times are calendar days from receipt of a purchase order. Add 3 calendar days for shipping to the port of delivery. 5. Expedited orders Expediting costs 10 percent of the goods value and saves 2 calendar days.

> Gulfstream Pumpworks: conditions of sale Issued 3 March 2026. Synthetic demonstration document. 1. Prices and currency All prices are quoted in United States dollars (USD), ex works. 2. Minimum order The minimum order value is USD 500. Each part also carries a minimum order quantity, shown in the catalogue. Quantities below it are raised to the minimum and charged in full.

> 3. Payment Invoices are payable within 45 days of the invoice date. 4. Lead time Catalogue lead times are calendar days counted from order confirmation. Orders received after 12:00 Central European Time are confirmed on the next working day. Delivery to the vessel adds 2 calendar days for port clearance.

> 3. Payment Invoices are payable within 30 days of the invoice date. 4. Lead time Catalogue lead times are calendar days counted from order confirmation. Orders received after 15:00 Central European Time are confirmed on the next working day. Delivery to the vessel adds 2 calendar days for port clearance.

> Nordsee Marine Spares: terms of supply Issued 1 June 2026. Synthetic demonstration document. 1. Prices and currency All prices are quoted in euros (EUR) and exclude freight and duties. 2. Minimum order value The minimum order value is EUR 400. Smaller orders are not accepted.

Label: 

## 9. spares-procurement/T13 (expected: refuse)

**Question:** When will the wear ring be delivered?

**Key facts:** none

**Reply (refused):** I cannot help with delivery times. Please contact your manager or the responsible department for more information.

**Evidence:**

> part_no: G-BG40-030-AM; description: Wear ring, aftermarket; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 125.61; currency: USD; lead_time_days: 3; moq: 1; in_stock: no

> part_no: N-BG40-030-AM; description: Wear ring, aftermarket; equipment: bilge pump BG-40; supplier: Nordsee Marine Spares; unit_price: 127.18; currency: EUR; lead_time_days: 11; moq: 1; in_stock: yes

> part_no: N-CW150-030-AM; description: Wear ring, aftermarket; equipment: cooling water pump CW-150; supplier: Nordsee Marine Spares; unit_price: 685.61; currency: EUR; lead_time_days: 6; moq: 1; in_stock: yes

> 6. Returns Unused parts may be returned within 30 days with a 20 percent restocking fee.

> part_no: N-BG40-030-OE; description: Wear ring, OEM; equipment: bilge pump BG-40; supplier: Nordsee Marine Spares; unit_price: 193.08; currency: EUR; lead_time_days: 12; moq: 1; in_stock: no

Label: 

## 10. spares-procurement/T16 (expected: answer)

**Question:** What is the part number and description for the ballast pump BP-200 impeller?

**Key facts:** The part number is N-BP200-020-AM.; The description is Impeller, bronze, 230 mm, aftermarket.

**Reply (answered):** G-BP200-020-AM: Impeller, bronze, 230 mm, aftermarket

**Evidence:**

> part_no: G-BP200-020-AM; description: Impeller, bronze, 230 mm, aftermarket; equipment: ballast pump BP-200; supplier: Gulfstream Pumpworks; unit_price: 443.59; currency: USD; lead_time_days: 5; moq: 1; in_stock: no

> part_no: G-BP200-021-OE; description: Impeller, stainless steel, 230 mm, OEM; equipment: ballast pump BP-200; supplier: Gulfstream Pumpworks; unit_price: 799.26; currency: USD; lead_time_days: 16; moq: 1; in_stock: no

> part_no: N-BP200-020-AM; description: Impeller, bronze, 230 mm, aftermarket; equipment: ballast pump BP-200; supplier: Nordsee Marine Spares; unit_price: 426.16; currency: EUR; lead_time_days: 5; moq: 1; in_stock: no

> part_no: N-BP200-021-OE; description: Impeller, stainless steel, 230 mm, OEM; equipment: ballast pump BP-200; supplier: Nordsee Marine Spares; unit_price: 719.00; currency: EUR; lead_time_days: 11; moq: 1; in_stock: yes

> part_no: G-BP200-020-OE; description: Impeller, bronze, 230 mm, OEM; equipment: ballast pump BP-200; supplier: Gulfstream Pumpworks; unit_price: 565.24; currency: USD; lead_time_days: 18; moq: 1; in_stock: yes

Label: 

## 11. spares-procurement/T10 (expected: refuse)

**Question:** How long will it take to deliver my order if I place it now?

**Key facts:** none

**Reply (refused):** I can't find that in the catalogue or supplier terms. Try rephrasing, or ask your manager or the responsible department. You may want to check the catalogue for the lead time of the specific parts in your order, or contact the supplier directly for their current delivery times.

**Evidence:**

> 3. Payment Invoices are payable within 30 days of the invoice date. 4. Lead time Catalogue lead times are calendar days counted from order confirmation. Orders received after 15:00 Central European Time are confirmed on the next working day. Delivery to the vessel adds 2 calendar days for port clearance.

> 3. Payment Payment is due within 30 days of shipment. 4. Lead time Catalogue lead times are calendar days from receipt of a purchase order. Add 3 calendar days for shipping to the port of delivery. 5. Expedited orders Expediting costs 10 percent of the goods value and saves 2 calendar days.

> 3. Payment Invoices are payable within 45 days of the invoice date. 4. Lead time Catalogue lead times are calendar days counted from order confirmation. Orders received after 12:00 Central European Time are confirmed on the next working day. Delivery to the vessel adds 2 calendar days for port clearance.

> 3. Approval A purchaser may approve orders up to 2,000 in the order currency. A technical superintendent approves orders above 2,000 and up to 10,000. The fleet manager approves orders above 10,000. 4. Currency Each purchase order is raised in the currency quoted by the supplier.

> Gulfstream Pumpworks: conditions of sale Issued 3 March 2026. Synthetic demonstration document. 1. Prices and currency All prices are quoted in United States dollars (USD), ex works. 2. Minimum order The minimum order value is USD 500. Each part also carries a minimum order quantity, shown in the catalogue. Quantities below it are raised to the minimum and charged in full.

Label: 

## 12. mlc-crew-rights/S10 (expected: answer)

**Question:** What is the requirement for the number of seafarers on board a ship according to the document?

**Key facts:** Ships must have a sufficient number of seafarers to ensure safe operation.

**Reply (answered):** The requirement for the number of seafarers on board a ship is that it must be sufficient to ensure the safe, efficient, and secure operation of the ship, taking into account concerns about seafarer fatigue and the particular nature and conditions of the voyage. [C3] "1. Each Member shall require that all ships that fly its flag have a sufficient number of seafarers employed on board to ensure that ships are operated safely, efficiently and with due regard to security under all conditions, taking into account concerns about seafarer fatigue and the particular nature and conditions of the voyage."

**Evidence:**

> Standard A2.7 – Manning levels 1. Each Member shall require that all ships that fly its flag have a sufficient number of seafarers on board to ensure that ships are operated safely, efficiently and with due regard to security. Every ship shall be manned by a crew that is adequate, in terms of size and qualifications, to ensure the safety and security of the ship and its personnel, under all operating conditions, in accordance with the minimum safe

> when off duty, which are of adequate area having regard to the size of the ship and the number of seafarers on board. 15. All ships shall be provided with separate offices or a common ship’s office for use by deck and engine departments; ships of less than 3,000 gross tonnage may be exempted by the competent authority from this requirement after consultation with the shipowners’ and seafarers’ organizations concerned. 16. Ships regularly trading to mosquito-infested ports shall be fitted with appropriate devices as required by the competent authority. 17. Appropriate seafarers’ recreational facilities, amenities and services, including social connectivity, as adapted to meet the special needs of seafarers who must live and work on ships, shall be provided on board for the benefit of all seafarers, taking into account Regulation 4.3 and the associated Code provisions on health and safety protection and accident prevention. 18. The competent authority shall require frequent inspections to be carried out on board ships, by or under the authority of the master, to ensure that seafarer accommodation is clean, decently habitable and maintained in a good state of repair. The results of each such inspection shall be recorded and be available for review.

> Regulation 2.7 – Manning levels Purpose: To ensure that seafarers work on board ships with sufficient personnel for the safe, efficient and secure operation of the ship 1. Each Member shall require that all ships that fly its flag have a sufficient number of seafarers employed on board to ensure that ships are operated safely, efficiently and with due regard to security under all conditions, taking into account concerns about seafarer fatigue and the particular nature and conditions of the voyage.

> Standard A2.1 – Seafarers’ employment agreements 1. Each Member shall adopt laws or regulations requiring that ships that fly its flag comply with the following requirements: (a) seafarers working on ships that fly its flag shall have a seafarers’ employment agreement signed by both the seafarer and the shipowner or a representative of the shipowner (or, where they are not employees, evidence of contractual or similar arrangements) providing them with decent working and living conditions on board the ship as required by this Convention; (b) seafarers signing a seafarers’ employment agreement shall be given an opportunity to examine and seek advice on the agreement before signing, as well as such other facilities as are necessary to ensure that they have freely entered into an agreement with a sufficient understanding of their rights and responsibilities; (c) the shipowner and seafarer concerned shall each have a signed original of the seafarers’ employment agreement; (d) measures shall be taken to ensure that clear information as to the conditions of their employment can be easily obtained on board by seafarers, including the ship’s master, and that such information, including a copy of the seafarers’ employment agreement, is also accessible for review by officers of a competent authority, including those in ports to be visited; and (e) seafarers shall be given a document containing a record of their employment on board the ship. 2. Where a collective bargaining agreement forms all or part of a seafarers’ employment agreement, a copy of that agreement shall be available on board. Where the language of the seafarers’ employment agreement and any applicable collective

> 102 AppEndix A5-I The working and living conditions of seafarers that must be inspected and approved by the flag State before certifying a ship in accordance with Standard A5.1.3, paragraph 1: Minimum age Medical certification Qualifications of seafarers Seafarers’ employment agreements Use of any licensed or certified or regulated private recruitment and placement service Hours of work or rest Manning levels for the ship Accommodation On-board recreational facilities Food and catering Health and safety and accident prevention On-board medical care On-board complaint procedures Payment of wages Financial security for repatriation Financial security relating to shipowners’ liability

Label: 

## 13. mlc-crew-rights/S01 (expected: answer)

**Question:** What measures must be included in the laws and regulations to ensure the safety and health of seafarers according to Standard A4.3?

**Key facts:** The measures should include the adoption and effective implementation and promotion of occupational safety and health policies and programmes on ships that fly the Member’s flag, including risk evaluation as well as training and instruction of seafarers.; The measures should include reasonable precautions to prevent occupational accidents, injuries and diseases on board ship, including through the provision of all necessary appropriately-sized personal protective equipment and measures to reduce and prevent the risk of exposure to harmful levels of ambient factors and chemicals, as well as the risk of injury or disease that may arise from the use of equipment and machinery on board ships.; The measures should include on-board programmes for the prevention of occupational accidents, injuries and diseases and for continuous improvement in occupational safety and health protection, involving seafarers’ representatives and all other persons concerned in their implementation, taking account of preventive measures, including engineering and design control, substitution of processes and procedures for collective and individual tasks, and the use of personal protective equipment.

**Reply (answered):** The laws and regulations and other measures to be adopted in accordance with Regulation 4.3, paragraph 3, shall include the following subjects: (a) the adoption and effective implementation and promotion of occupational safety and health policies and programmes on ships that fly the Member’s flag, including risk evaluation as well as training and instruction of seafarers; (b) reasonable precautions to prevent occupational accidents, injuries and diseases on board ship, including through the provision of all necessary appropriately-sized personal protective equipment and measures to reduce and prevent the risk of exposure to harmful levels of ambient factors and chemicals, as well as the risk of injury or disease that may arise from the use of equipment and machinery on board ships; (c) on-board programmes for the prevention of occupational accidents, injuries and diseases and for continuous improvement in occupational safety and health protection, involving seafarers’ representatives and all other persons concerned in their implementation, taking account of preventive measures, including engineering and design control, substitution of processes and procedures for collective and individual tasks, and the use of personal protective equipment; and (d) requirements for inspecting, reporting and correcting unsafe conditions and for investigating and reporting on-board occupational accidents. [C1] (file: mlc_2006_consolidated_2022.pdf) "the adoption and effective implementation and promotion of occupational safety and health policies and programmes on ships that fly the Member’s flag, including risk evaluation as well as training and instruction of seafarers;"

**Evidence:**

> Standard A4.3 – Health and safety protection and accident prevention 1. The laws and regulations and other measures to be adopted in accordance with Regulation 4.3, paragraph 3, shall include the following subjects: (a) the adoption and effective implementation and promotion of occupational safety and health policies and programmes on ships that fly the Member’s flag, including risk evaluation as well as training and instruction of seafarers; (b) reasonable precautions to prevent occupational accidents, injuries and diseases on board ship, including through the provision of all necessary appropriately-sized personal protective equipment and measures to reduce and prevent the risk of exposure to harmful levels of ambient factors and chemicals, as well as the risk of injury or disease that may arise from the use of equipment and machinery on board ships; (c) on-board programmes for the prevention of occupational accidents, injuries and diseases and for continuous improvement in occupational safety and health protection, involving seafarers’ representatives and all other persons concerned in their implementation, taking account of preventive measures, including engineering and design control, substitution of processes and procedures for collective and individual tasks, and the use of personal protective equipment; and (d) requirements for inspecting, reporting and correcting unsafe conditions and for investigating and reporting on-board occupational accidents. 2. The provisions referred to in paragraph 1 of this Standard shall: (a) take account of relevant international instruments dealing with occupational safety and health protection in general and with specific risks, and address all matters relevant to the prevention of occupational accidents, injuries and diseases that may be applicable to the work of seafarers and particularly those which are specific to maritime employment; (b) clearly specify the obligation of shipowners, seafarers and others concerned to comply with the applicable standards and with the ship’s occupational safety and

> Standard A3.1 – Accommodation and recreational facilities 1. Each Member shall adopt laws and regulations requiring that ships that fly its flag: (a) meet minimum standards to ensure that any accommodation for seafarers, working or living on board, or both, is safe, decent and in accordance with the relevant provisions of this Standard; and (b) are inspected to ensure initial and ongoing compliance with those standards. 2. In developing and applying the laws and regulations to implement this Standard, the competent authority, after consulting the shipowners’ and seafarers’ organizations concerned, shall: (a) take into account Regulation 4.3 and the associated Code provisions on health and safety protection and accident prevention, in light of the specific needs of seafarers that both live and work on board ship; and (b) give due consideration to the guidance contained in Part B of this Code. 3. The inspections required under Regulation 5.1.4 shall be carried out when:

> 67 Health protection, medical care, welfare and social security protection health policy and programme with special attention being paid to the safety and health of seafarers under the age of 18; (c) specify the duties of the master or a person designated by the master, or both, to take specific responsibility for the implementation of and compliance with the ship’s occupational safety and health policy and programme; and (d) specify the authority of the ship’s seafarers appointed or elected as safety representatives to participate in meetings of the ship’s safety committee. Such a committee shall be established on board a ship on which there are five or more seafarers. 3. The laws and regulations and other measures referred to in Regulation 4.3, paragraph 3, shall be regularly reviewed in consultation with the representatives of the shipowners’ and seafarers’ organizations and, if necessary, revised to take account of changes in technology and research in order to facilitate continuous improvement in occupational safety and health policies and programmes and to provide a safe occupational environment for seafarers on ships that fly the Member’s flag. 4. Compliance with the requirements of applicable international instruments on the acceptable levels of exposure to workplace hazards on board ships and on the development and implementation of ships’ occupational safety and health policies and programmes shall be considered as meeting the requirements of this Convention. 5. Each Member shall ensure that: (a) all deaths of seafarers employed, engaged or working on board ships that fly its flag are adequately investigated and recorded, and reported on an annual basis to the Director-General of the International Labour Office to be published in a global register; (b) occupational accidents, injuries and diseases are adequately reported, taking into account the guidance provided by the International Labour Organization with respect to the reporting and recording of occupational accidents and diseases; (c) comprehensive statistics of such accidents and diseases are kept, analysed and published and, where appropriate, followed up by research into general trends and into the hazards identified; and (d) occupational accidents are investigated. 6. Reporting and investigation of occupational safety and health matters shall be designed to ensure the protection of seafarers’ personal data, and shall take account

> 72 Maritime Labour Convention, 2006 2. Relevant provisions or recommendations adopted by the appropriate national authorities or organizations or international organizations should be taken into account by those preparing texts of occupational safety and health protection and accident prevention measures or recommended practices. 3. In formulating occupational safety and health protection and accident prevention programmes, each Member should have due regard to any code of practice concerning the safety and health of seafarers which may have been published by the International Labour Organization.

> Standard A4.1 – Medical care on board ship and ashore 1. Each Member shall ensure that measures providing for health protection and medical care, including essential dental care, for seafarers working on board a ship that flies its flag are adopted which: (a) ensure the application to seafarers of any general provisions on occupational health protection and medical care relevant to their duties, as well as of special provisions specific to work on board ship; (b) ensure that seafarers are given health protection and medical care as comparable as possible to that which is generally available to workers ashore, including prompt access to the necessary medicines, medical equipment and facilities for diagnosis and treatment and to medical information and expertise; (c) give seafarers the right to visit a qualified medical doctor or dentist without delay in ports of call, where practicable; (d) ensure that, to the extent consistent with the Member’s national law and practice, medical care and health protection services while a seafarer is on board ship or landed in a foreign port are provided free of charge to seafarers; and (e) are not limited to treatment of sick or injured seafarers but include measures of a preventive character such as health promotion and health education programmes.

Label: 

## 14. spares-procurement/S05 (expected: answer)

**Question:** How long is the lead time for the aftermarket impeller, and is it in stock?

**Key facts:** The lead time for the aftermarket impeller is 4 days.; The aftermarket impeller is not in stock.

**Reply (answered):** The lead time for the aftermarket impeller is 11 days, and it is not in stock. [C1] "Impeller, bronze, 230 mm, aftermarket; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 429.34; currency: USD; lead_time_days: 11; moq: 1; in_stock: no"

**Evidence:**

> part_no: G-BG40-020-AM; description: Impeller, bronze, 230 mm, aftermarket; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 429.34; currency: USD; lead_time_days: 11; moq: 1; in_stock: no

> part_no: G-CW150-020-AM; description: Impeller, bronze, 230 mm, aftermarket; equipment: cooling water pump CW-150; supplier: Gulfstream Pumpworks; unit_price: 591.81; currency: USD; lead_time_days: 4; moq: 1; in_stock: yes

> part_no: N-CW150-021-AM; description: Impeller, stainless steel, 230 mm, aftermarket; equipment: cooling water pump CW-150; supplier: Nordsee Marine Spares; unit_price: 149.50; currency: EUR; lead_time_days: 7; moq: 1; in_stock: no

> 3. Payment Payment is due within 30 days of shipment. 4. Lead time Catalogue lead times are calendar days from receipt of a purchase order. Add 3 calendar days for shipping to the port of delivery. 5. Expedited orders Expediting costs 10 percent of the goods value and saves 2 calendar days.

> part_no: G-CW150-021-AM; description: Impeller, stainless steel, 230 mm, aftermarket; equipment: cooling water pump CW-150; supplier: Gulfstream Pumpworks; unit_price: 135.36; currency: USD; lead_time_days: 4; moq: 1; in_stock: yes

Label: 

## 15. mlc-crew-rights/T15 (expected: answer)

**Question:** What are the rules for splitting the rest periods and what happens if rest is lost due to an emergency?

**Key facts:** Daily rest may be split into no more than two periods, one of which is at least 6 hours.; Rest lost because of a drill or an emergency is made up with compensatory rest.

**Reply (answered):** According to the Maritime Labour Convention, 2006, hours of rest may be divided into no more than two periods, one of which shall be at least six hours in length, and the interval between consecutive periods of rest shall not exceed 14 hours [C2]. If rest is lost due to an emergency, it is made up with compensatory rest [C1].

**Evidence:**

> # 2. Hours of rest Every crew member receives at least 10 hours of rest in any 24-hour period and at least 77 hours in any seven-day period. Daily rest may be split into no more than two periods, one of which is at least 6 hours. Each crew member signs the record of rest hours at the end of every month and keeps a copy. Rest lost because of a drill or an emergency is made up with compensatory rest.

> 32 Maritime Labour Convention, 2006 4. In determining the national standards, each Member shall take account of the danger posed by the fatigue of seafarers, especially those whose duties involve navigational safety and the safe and secure operation of the ship. 5. The limits on hours of work or rest shall be as follows: (a) maximum hours of work shall not exceed: (i) 14 hours in any 24-hour period; and (ii) 72 hours in any seven-day period; or (b) minimum hours of rest shall not be less than: (i) ten hours in any 24-hour period; and (ii) 77 hours in any seven-day period. 6. Hours of rest may be divided into no more than two periods, one of which shall be at least six hours in length, and the interval between consecutive periods of rest shall not exceed 14 hours. 7. Musters, fire-fighting and lifeboat drills, and drills prescribed by national laws and regulations and by international instruments, shall be conducted in a manner that minimizes the disturbance of rest periods and does not induce fatigue. 8. When a seafarer is on call, such as when a machinery space is unattended, the seafarer shall have an adequate compensatory rest period if the normal period of rest is disturbed by call-outs to work. 9. If no collective agreement or arbitration award exists or if the competent authority determines that the provisions in the agreement or award in respect of paragraph 7 or 8 of this Standard are inadequate, the competent authority shall determine such provisions to ensure the seafarers concerned have sufficient rest. 10. Each Member shall require the posting, in an easily accessible place, of a table with the shipboard working arrangements, which shall contain for every position at least: (a) the schedule of service at sea and service in port; and (b) the maximum hours of work or the minimum hours of rest required by national laws or regulations or applicable collective agreements. 11. The table referred to in paragraph 10 of this Standard shall be established in a standardized format in the working language or languages of the ship and in English. 12. Each Member shall require that records of seafarers’ daily hours of work

> Regulation 2.3 – Hours of work and hours of rest Purpose: To ensure that seafarers have regulated hours of work or hours of rest 1. Each Member shall ensure that the hours of work or hours of rest for seafarers are regulated. 2. Each Member shall establish maximum hours of work or minimum hours of rest over given periods that are consistent with the provisions in the Code.

> 33 Conditions of employment take account of more frequent or longer leave periods or the granting of compensatory leave for watchkeeping seafarers or seafarers working on board ships on short voyages. 14. Nothing in this Standard shall be deemed to impair the right of the master of a ship to require a seafarer to perform any hours of work necessary for the immediate safety of the ship, persons on board or cargo, or for the purpose of giving assistance to other ships or persons in distress at sea. Accordingly, the master may suspend the schedule of hours of work or hours of rest and require a seafarer to perform any hours of work necessary until the normal situation has been restored. As soon as practicable after the normal situation has been restored, the master shall ensure that any seafarers who have performed work in a scheduled rest period are provided with an adequate period of rest.

> Guideline B2.3 – Hours of work and hours of rest Guideline B2.3.1 – Young seafarers 1. At sea and in port the following provisions should apply to all young seafarers under the age of 18: (a) working hours should not exceed eight hours per day and 40 hours per week and overtime should be worked only where unavoidable for safety reasons; (b) sufficient time should be allowed for all meals, and a break of at least one hour for the main meal of the day should be assured; and (c) a 15-minute rest period as soon as possible following each two hours of continuous work should be allowed. 2. Exceptionally, the provisions of paragraph 1 of this Guideline need not be applied if: (a) they are impracticable for young seafarers in the deck, engine room and catering departments assigned to watchkeeping duties or working on a rostered shift-work system; or (b) the effective training of young seafarers in accordance with established programmes and schedules would be impaired. 3. Such exceptional situations should be recorded, with reasons, and signed by the master. 4. Paragraph 1 of this Guideline does not exempt young seafarers from the general obligation on all seafarers to work during any emergency as provided for in

Label: 

## 16. spares-procurement/S02 (expected: refuse)

**Question:** When will the next port call for the supply ship be?

**Key facts:** none

**Reply (refused):** I cannot help with delivery times or vessel port calls. Please contact your manager or the responsible department for this information.

**Evidence:**

> 3. Payment Invoices are payable within 30 days of the invoice date. 4. Lead time Catalogue lead times are calendar days counted from order confirmation. Orders received after 15:00 Central European Time are confirmed on the next working day. Delivery to the vessel adds 2 calendar days for port clearance.

> 3. Payment Invoices are payable within 45 days of the invoice date. 4. Lead time Catalogue lead times are calendar days counted from order confirmation. Orders received after 12:00 Central European Time are confirmed on the next working day. Delivery to the vessel adds 2 calendar days for port clearance.

> Fleet procurement policy Version 4, effective 1 April 2026. Synthetic demonstration document. 1. Scope This policy covers spare parts ordered for vessels in the fleet. 2. Quotations Compare at least two suppliers where two list the part. Orders with a goods value above 5,000 in the order currency need two written quotations.

> 3. Payment Payment is due within 30 days of shipment. 4. Lead time Catalogue lead times are calendar days from receipt of a purchase order. Add 3 calendar days for shipping to the port of delivery. 5. Expedited orders Expediting costs 10 percent of the goods value and saves 2 calendar days.

> Nordsee Marine Spares: terms of supply Issued 1 June 2026. Synthetic demonstration document. 1. Prices and currency All prices are quoted in euros (EUR) and exclude freight and duties. 2. Minimum order value The minimum order value is EUR 400. Smaller orders are not accepted.

Label: 

## 17. spares-procurement/T19 (expected: answer)

**Question:** What is the unit price of the Shaft sleeve, aftermarket for the ballast pump BP-200 and what is the lead time in days?

**Key facts:** The unit price is 572.99 EUR.; The lead time is 5 days.

**Reply (answered):** The unit price of the Shaft sleeve, aftermarket for the ballast pump BP-200 is $569.51. The lead time is 12 days.

**Evidence:**

> part_no: G-BP200-040-AM; description: Shaft sleeve, aftermarket; equipment: ballast pump BP-200; supplier: Gulfstream Pumpworks; unit_price: 569.51; currency: USD; lead_time_days: 12; moq: 1; in_stock: no

> part_no: N-BP200-040-AM; description: Shaft sleeve, aftermarket; equipment: ballast pump BP-200; supplier: Nordsee Marine Spares; unit_price: 572.99; currency: EUR; lead_time_days: 5; moq: 1; in_stock: no

> part_no: G-BP200-040-OE; description: Shaft sleeve, OEM; equipment: ballast pump BP-200; supplier: Gulfstream Pumpworks; unit_price: 815.46; currency: USD; lead_time_days: 11; moq: 1; in_stock: yes

> part_no: N-BP200-090-AM; description: Pump shaft, aftermarket; equipment: ballast pump BP-200; supplier: Nordsee Marine Spares; unit_price: 416.05; currency: EUR; lead_time_days: 4; moq: 1; in_stock: no

> part_no: N-BP200-040-OE; description: Shaft sleeve, OEM; equipment: ballast pump BP-200; supplier: Nordsee Marine Spares; unit_price: 947.82; currency: EUR; lead_time_days: 10; moq: 1; in_stock: yes

Label: 

## 18. spares-procurement/S08 (expected: clarify)

**Question:** What is the unit price of the impeller for the bilge pump BG-40?

**Key facts:** The aftermarket impeller costs 453.72 EUR.; The OEM impeller costs 537.40 EUR.

**Reply (answered):** The unit price of the impeller for the bilge pump BG-40 is $429.34 for the aftermarket bronze impeller, $673.02 for the OEM bronze impeller, and $537.40 for the OEM bronze impeller from Nordsee Marine Spares.

**Evidence:**

> part_no: G-BG40-020-AM; description: Impeller, bronze, 230 mm, aftermarket; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 429.34; currency: USD; lead_time_days: 11; moq: 1; in_stock: no

> part_no: G-BG40-020-OE; description: Impeller, bronze, 230 mm, OEM; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 673.02; currency: USD; lead_time_days: 12; moq: 1; in_stock: yes

> part_no: N-BG40-020-OE; description: Impeller, bronze, 230 mm, OEM; equipment: bilge pump BG-40; supplier: Nordsee Marine Spares; unit_price: 537.40; currency: EUR; lead_time_days: 16; moq: 1; in_stock: no

> part_no: G-BG40-021-AM; description: Impeller, stainless steel, 230 mm, aftermarket; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 55.62; currency: USD; lead_time_days: 9; moq: 1; in_stock: yes

> part_no: G-BG40-021-OE; description: Impeller, stainless steel, 230 mm, OEM; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 75.82; currency: USD; lead_time_days: 12; moq: 1; in_stock: yes

Label: 

## 19. spares-procurement/T17 (expected: answer)

**Question:** What is the part number and unit price for the mechanical seal used in the BG-40 bilge pump?

**Key facts:** The part number is N-BG40-010-OE.; The unit price is 260.37 EUR.

**Reply (answered):** G-BG40-010-OE, $282.70

**Evidence:**

> part_no: G-BG40-010-OE; description: Mechanical seal, 45 mm, carbon/ceramic, OEM; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 282.70; currency: USD; lead_time_days: 11; moq: 1; in_stock: no

> part_no: G-BG40-010-AM; description: Mechanical seal, 45 mm, carbon/ceramic, aftermarket; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 173.63; currency: USD; lead_time_days: 9; moq: 1; in_stock: yes

> part_no: G-BG40-011-OE; description: Mechanical seal, 45 mm, silicon carbide, OEM; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 568.65; currency: USD; lead_time_days: 14; moq: 1; in_stock: yes

> part_no: N-BG40-010-OE; description: Mechanical seal, 45 mm, carbon/ceramic, OEM; equipment: bilge pump BG-40; supplier: Nordsee Marine Spares; unit_price: 260.37; currency: EUR; lead_time_days: 12; moq: 1; in_stock: yes

> part_no: G-BG40-011-AM; description: Mechanical seal, 45 mm, silicon carbide, aftermarket; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 391.24; currency: USD; lead_time_days: 4; moq: 1; in_stock: yes

Label: 

## 20. spares-procurement/S10 (expected: answer)

**Question:** What is the lead time and minimum order quantity for the impeller part N-BG40-020-OE?

**Key facts:** The lead time is 16 days.; The minimum order quantity is 1.

**Reply (answered):** 16 days, 1 unit

**Evidence:**

> part_no: N-BG40-020-OE; description: Impeller, bronze, 230 mm, OEM; equipment: bilge pump BG-40; supplier: Nordsee Marine Spares; unit_price: 537.40; currency: EUR; lead_time_days: 16; moq: 1; in_stock: no

> part_no: N-BG40-020-AM; description: Impeller, bronze, 230 mm, aftermarket; equipment: bilge pump BG-40; supplier: Nordsee Marine Spares; unit_price: 453.72; currency: EUR; lead_time_days: 4; moq: 1; in_stock: no

> part_no: G-BG40-020-AM; description: Impeller, bronze, 230 mm, aftermarket; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 429.34; currency: USD; lead_time_days: 11; moq: 1; in_stock: no

> part_no: G-BG40-020-OE; description: Impeller, bronze, 230 mm, OEM; equipment: bilge pump BG-40; supplier: Gulfstream Pumpworks; unit_price: 673.02; currency: USD; lead_time_days: 12; moq: 1; in_stock: yes

> part_no: N-BG40-021-OE; description: Impeller, stainless steel, 230 mm, OEM; equipment: bilge pump BG-40; supplier: Nordsee Marine Spares; unit_price: 75.64; currency: EUR; lead_time_days: 16; moq: 1; in_stock: yes

Label: 
