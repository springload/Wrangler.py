import wrangler.Page as baseClass

class LandingPage(baseClass.Page):
	
    def before_render(self):
        # print self.data
        return False

    
