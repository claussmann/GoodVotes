from goodvotes import *


@app.before_first_request
def initialization_code():
    service.create_admin_if_not_exists()

@app.route('/')
def start_page():
    user = False
    return render_template('start.html', user=user)


# @app.route('/login', methods=['POST'])
# def login():
#     username = request.form.get('username')
#     password = request.form.get('passwd')

#     token = service.get_session_token(username, password)
#     response = make_response(render_template('done.html', forward="/"))
#     response.set_cookie('token', value=token, secure=True, httponly=True)
#     return response


# @app.route('/logout', methods=['POST'])
# def logout():
#     service.terminate_user_session(request.cookies.get('token'))
#     response = make_response(render_template('done.html', forward="/", user=False))
#     response.set_cookie('token', value="None", secure=True, httponly=True, expires=0)
#     return response


# @app.route('/changepasswd', methods=['POST'])
# def change_passwd():
#     user = check_user()
#     password = request.form.get('passwd')
#     new_password = request.form.get('new_passwd')
#     confirm_password = request.form.get('confirm_passwd')
#     service.change_password(user, password, new_password, confirm_password)
#     return render_template('done.html', user=user, forward="/")


@app.route('/done')
def done_page():
    user = False
    return render_template('done.html', user=user, forward="/")


@app.route('/createnew', methods=['POST'])
def create_new_election():
    user = False
    candidates = set()
    for i in range(1, 13):
        c = request.form.get('candidate%d' % i)
        if c != None and c != "" and not c.isspace():
            candidates.add(c)
    election = service.register_election(
        request.form.get('name'),
        request.form.get('description'),
        candidates,
        int(request.form.get('committeesize')),
        user
    )
    app.logger.info("Election registered: %s, %d candidates, committee size: %d" % (
        election.title, len(election.candidates), election.committeesize))
    return render_template('done.html', user=user, forward="/details/" + str(election.id))


@app.route('/searchforelection')
def search_election():
    user = False
    keyword = request.args.get('keyword')
    matching_elections = service.search(keyword)
    return render_template('search_results.html', keyword=keyword, elections=matching_elections, user=user)


@app.route('/details/<electionID>')
def details_page(electionID):
    user = False
    election = service.get_election(electionID)
    # if user and user.owns_election(electionID):
    service.evaluate(electionID, user)
    return render_template('details.html', election=election, admin=True, user=user)
    # return render_template('details.html', election=election, admin=False, user=user)


@app.route('/vote/<electionID>')
def voting_page(electionID):
    user = False
    return render_template('vote.html', election=service.get_election(electionID), user=user)


@app.route('/vote/<electionID>', methods=['POST'])
def add_vote(electionID):
    content = request.get_json()
    try:
        sets = content["sets"]
        bounds = content["bounds"]
        bounded_sets = list()
        for s in sets:
            items_in_set = set(sets[s])
            if len(items_in_set) == 0:
                continue
            bounded_sets.append(service.BoundedSet(bounds[s][0], bounds[s][1], bounds[s][2], items_in_set))

        votesstring = ("%s  " * len(bounded_sets)) % tuple([str(s) for s in bounded_sets])
        app.logger.debug("New vote received: " + votesstring)
        ballot = service.BoundedApprovalBallot()
        ballot.encode(bounded_sets)
        service.add_vote(electionID, ballot)
    except Exception as e:
        app.logger.warn(e)
        return "something is wrong with the data", 400
    return "OK"


@app.route('/evaluate/<electionID>', methods=['POST'])
def evaluate(electionID):
    user = False
    election = service.get_election(electionID)
    best_committee = service.evaluate(electionID, user)
    service.stop_election(electionID, user)
    app.logger.info("Election stopped by creator: %s (%s)" % (election.id, election.title))
    return render_template('done.html', user=user, forward="/details/" + electionID)


@app.route('/delete/<electionID>', methods=['POST'])
def deletion_successful_page(electionID):
    user = False
    service.delete_election(electionID, user)
    app.logger.info("Results deleted by creator: %s" % str(electionID))
    return render_template('done.html', user=user, forward="/")


@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(400)
def page_not_found(e):
    return render_template('errors/400.html'), 400


@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    print(e)
    return render_template("errors/500.html", exception=e), 500

