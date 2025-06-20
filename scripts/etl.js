const fs = require('fs');

// take the city as command line argument
const city = process.argv[2];

// iterate through all the json files in the data folder

const files = fs.readdirSync('./data');
const events = [];
files.forEach(file => {
    console.log(file);
    const data = fs.readFileSync(`./data/${file}`);
    // extract the beginning of the file name to get the category delimited by an underscore
    const category = file.split('_')[0];
    const json = JSON.parse(data);
    const events_results = json.events_results;
    if (events_results) {
        events_results.forEach(event => {
            // add the category to the event object
            event.category = category;
            events.push(event);
        })
    }
})

/* {
      "title": "Techno Painting Workshop",
      "date": {
        "start_date": "Sep 3",
        "when": "Sun, Sep 3, 4 – 7 PM"
      },
      "address": [
        "Brunnenstraße 186",
        "Berlin, Germany"
      ],
      "link": "https://www.eventbrite.com/e/techno-painting-workshop-tickets-681533985497",
      "event_location_map": {
        "image": "https://www.google.com/maps/vt/data=TbRQzjn1ZvJ517qqzk4Y5VPf0HkiZkm_IXrQKhKKIJxUJph8LRctKgLK8qa0wBhTsk20NuUwU61PR5XDgHOgTYzpYAgRZXaqne05JpKZYltQ7NEyQhY",
        "link": "https://www.google.com/maps/place//data=!4m2!3m1!1s0x47a851e51eb04c91:0x517309930ff6dd35?sa=X&ved=2ahUKEwi5gZG30IaBAxVljIkEHSW1CNY4FBD14gF6BAgBEAA",
        "serpapi_link": "https://serpapi.com/search.json?data=%214m2%213m1%211s0x47a851e51eb04c91%3A0x517309930ff6dd35&engine=google_maps&google_domain=google.com&hl=en&q=Art&start=20&type=place"
      },
      "description": "Unleash your creativity! Experience a flow state through art and music, and get an insiders view to Berlins unique Techno culture.",
      "ticket_info": [
        {
          "source": "Eventbrite.com",
          "link": "https://www.eventbrite.com/e/techno-painting-workshop-tickets-104043683458",
          "link_type": "tickets"
        },
        {
          "source": "Allevents.in",
          "link": "https://allevents.in/berlin/techno-painting-workshop/10000681533985497",
          "link_type": "tickets"
        }
      ],
      "thumbnail": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQyxog-hLYmNuAYFvyS_GpVhPeL818YTeooWt_QD5HUkooPV3NC5dv6HbU&s",
      "image": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRLwjjurs_Fdqr0S3LSYzo6ng9XaH0EMvS9XlraiJ_TzQ&s=10"
    } */

// transform the data to be in the format of the events table
// title, description, start time with date, end time with date, image, link, category, location link
// and remove other fields

const transformedEvents = events.map(event => {
    const { title, date, image, link, category, event_location_map } = event;
    // "Thu, Sep 21, 8 PM – Fri, Sep 22, 12 AM",
    // "Sun, Sep 24, 8 PM",
    // "Tue, Sep 5, 8:00 – 11:30 PM",
    // Sep 24 - Sep 25
    // the when field can have different formats, extract start date with time and end date with time
    const when = date.when;
    let start_date = null;
    let end_date = null;

    // if the when field has a -, it means it has a start date and end date
    if (when.includes('–')) {
        const [start_date_time, end_date_time] = when.split('–');

        // remove day of the week from the start_date_time if present
        start_date = start_date_time.replace(/(Mon|Tue|Wed|Thu|Fri|Sat|Sun), /, '').trim();

        // if start time has time with no am/pm, but the end time has am/pm, append the am/pm to the start time
        if (!start_date_time.toLowerCase().includes('am') && !start_date_time.toLowerCase().includes('pm') && (end_date_time.toLowerCase().includes('am') || end_date_time.toLowerCase().includes('pm'))) {
            start_date += ` ${end_date_time.split(' ')[2].trim()}`;
        }

        //regex to check if the end date has month  JAN, FEB etc
        const hasMonth = /[A-Z]{3}/.test(end_date_time);

        // if the end date has time and no date, concat the start date to it
        if (!end_date_time.includes(',') && !hasMonth) {
            // if the start date has no time, only date, then add the month from the start date to the end date else add the start date to the end date
            if (!start_date.includes(',') && end_date_time.trim().split(' ').length === 1) {
                end_date = `${start_date.split(' ')[0]} ${end_date_time.trim()}`;
            } else {
                end_date = `${start_date.split(',')[0]}, ${end_date_time.trim()}`;
            }

        } else {
            end_date = end_date_time.replace(/(Mon|Tue|Wed|Thu|Fri|Sat|Sun), /, '').trim();
        }
    } else {
        // remove day of the week from the start_date_time if present
        start_date = when.replace(/(Mon|Tue|Wed|Thu|Fri|Sat|Sun), /, '').trim();
    }

    //replace a.m. and p.m. with AM and PM
    start_date = start_date.replace('a.m.', 'AM').replace('p.m.', 'PM');
    end_date = end_date ? end_date.replace('a.m.', 'AM').replace('p.m.', 'PM') : null;

    //replace all times without : with :00
    start_date = start_date.replace(/(\d{1,2}) (AM|PM)/, '$1:00 $2');
    end_date = end_date ? end_date.replace(/(\d{1,2}) (AM|PM)/, '$1:00 $2') : null;

    // remove seconds place from the time if it has hours, minutes and seconds
    start_date = start_date.replace(/(\d{1,2}:\d{2}):\d{2} (AM|PM)/, '$1 $2');
    end_date = end_date ? end_date.replace(/(\d{1,2}:\d{2}):\d{2} (AM|PM)/, '$1 $2') : null;

    // if no end date is present and start_date contains a time
    // Sep 5, 8:00 PM
    // set the end date as the start date and add 2 hours to it using Date object
    if (!end_date && start_date.includes(':')) {
        const date = new Date(start_date);
        date.setHours(date.getHours() + 2);
        end_date = date.toLocaleString('en-US', { month: 'short', day: '2-digit', hour: 'numeric', minute: 'numeric', hour12: true });
    }

    // extract the location link from the event_location_map, handle if it is not present
    const location_link = event_location_map ? event_location_map.link : null;
    //merge the address array into a string and store it in location
    const location = event.address ? event.address.join(', ') : null;

    let description = event.description;
    // append the event link to the description, handle if description is not present
    if (link) {
        description = description ? `${description}     ${link}` : link;
    }


    return {
        title,
        description,
        start_date,
        end_date,
        image,
        link,
        category,
        location,
        location_link
    }
})

console.log(transformedEvents.length);

// deduplicate the events based on title, description, start_date, end_date, location_link 
// and for the duplicates append the category to the category field as an array
const dedupedEvents = [];
transformedEvents.forEach(event => {
    const { title, description, start_date, end_date, location_link, category } = event;
    const dedupedEvent = dedupedEvents.find(event => event.title === title && event.description === description && event.start_date === start_date && event.end_date === end_date);
    if (dedupedEvent) {
        // if the category is not already present in the category array, add it
        if (!dedupedEvent.category.includes(category)) {
            dedupedEvent.category.push(category);
        }
    } else {
        event.category = [category];
        dedupedEvents.push(event);
    }

})



// filter irrerelevant events, location doesn't contain Berlin
const filteredEvents = dedupedEvents.filter(event => {
    const { location } = event;
    return location && location.toLowerCase().includes(city);
})

console.log(filteredEvents.length);

// log the transformed data as a json 
// console.log(JSON.stringify(dedupedEvents, null, 2));

//save the transformed data to a csv file
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const csvWriter = createCsvWriter({
    path: './events.tsv',
    header: [
        { id: 'title', title: 'title' },
        { id: 'description', title: 'description' },
        { id: 'start_date', title: 'start_date' },
        { id: 'end_date', title: 'end_date' },
        { id: 'image', title: 'image' },
        { id: 'link', title: 'link' },
        { id: 'category', title: 'category' },
        { id: 'location', title: 'location' },
        { id: 'location_link', title: 'location_link' }
    ],
    fieldDelimiter: ';', // safest way to specify tab
    alwaysQuote: false
});


csvWriter.writeRecords(filteredEvents);

