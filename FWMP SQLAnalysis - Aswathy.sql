/* Creating Database */
Create database foodDB;
Use foodDB;

/* Imported the datasets to the DB using table import wizard */
Show tables;
# Primary and foreign keys were set using alter table feature

/* Questions to be Answered (SQL Queries & Analysis)
The project will analyze food donations, claims, and provider trends using SQL queries. Below are some key questions:*/

/*  Providers & Receivers */
#1. How many food providers and receivers are there in each city?
Select City, count(Provider_ID) from providers_data group by City;
Select City, count(Receiver_ID) from receivers_data group by City;

#2. Which type of food provider (restaurant, grocery store, etc.) contributes the most food?
Select Provider_Type, sum(Quantity) as total_contributed from food_listings_data 
group by provider_type order by total_contributed desc limit 1;
# Restaurant	6923

#3. What is the contact information of food providers in a specific city?
Select Name, Contact from providers_data where City = 'Adambury'; # Change city name based on requirement

#4. Which receivers have claimed the most food?
Select r.Receiver_ID, r.Name, count(c.claim_id) AS total_claimed
from claims_data c join receivers_data r on c.Receiver_ID = r.Receiver_ID 
where c.status ='Completed' group by r.Receiver_ID, r.Name order by total_claimed DESC;

/* Food Listings & Availability */
#5. What is the total quantity of food available from all providers?
Select sum(quantity) as total_quantity from food_listings_data;

#6. Which city has the highest number of food listings?
Select Location, count(*) as num_of_listings from food_listings_data group by Location order by num_of_listings desc;

#7. What are the most commonly available food types?
Select Food_Type, count((Food_Type)) as type_count from food_listings_data group by Food_Type order by type_count desc;

/* Claims & Distribution */
#8. How many food claims have been made for each food item?
Select f.Food_Name, c.Food_ID, COUNT(c.Food_ID) as num_claims 
from claims_data c join food_listings_data f 
on f.Food_ID = c.Food_ID group by Food_ID;

#9. Which provider has had the highest number of successful food claims?
Select p.Provider_ID, p.Name, count(*) as successful_claims from claims_data c
join food_listings_data f on c.Food_ID = f.Food_ID
join providers_data p on f.Provider_ID = p.Provider_ID
where c.Status = 'Completed' group by p.Provider_ID, p.Name
order by successful_claims desc;

#10. What percentage of food claims are completed vs. pending vs. canceled?
Select Status, count(*) * 100.0 / (select count(*) from claims_data) as percentage from claims_data
group by Status;

/* Analysis & Insights */
#11. What is the average quantity of food claimed per receiver?
Select avg(total_claimed) as average_claimed_per_receiver from (
    select Receiver_ID, sum(case when Status = 'Completed' then 1 else 0 end) as total_claimed
    from claims_data group by Receiver_ID
) as receiver_totals;

#12. Which meal type (breakfast, lunch, dinner, snacks) is claimed the most?
Select Meal_Type, count((Meal_Type)) as type_count from food_listings_data group by Meal_Type order by type_count desc;

#13. What is the total quantity of food donated by each provider?
Select sum(quantity) as total_quantity from food_listings_data;

/* Extra Analysis Done */
-- Food Listings that were never claimed
Select * from food_listings_data where food_ID not in (Select food_ID from claims_data);

# Most claimed food type
Select food_listings_data.Food_Type, count(*) as Total_Claimed from food_listings_data
join claims_data on food_listings_data.Food_ID = claims_data.Food_ID
group by food_listings_data.Food_Type order by Total_Claimed desc limit 1;

# Receivers with no claims
Select receivers_data.* from receivers_data
left join claims_data
on receivers_data.Receiver_ID = claims_data.Receiver_ID
where claims_data.Claim_ID is null;

# Providers with no claims
Select providers_data.* from providers_data
join food_listings_data on providers_data.Provider_ID = food_listings_data.Provider_ID
left join claims_data on food_listings_data.Food_ID = claims_data.Food_ID
where claims_data.Claim_ID is null;