import os
from PIL import Image, ImageOps
import random
from helpers import *
import re
import numpy as np
import matplotlib.pyplot as plt
import io
from PIL import Image
# -*- coding: utf-8 -*-
RE = re.compile(r"/\d+")

class ObjFile:

    """
    CREDIT ==> https://github.com/pclausen/obj2png
    """

    def __init__(self, obj_file=None):
        self.nodes = None
        self.faces = None
        if obj_file:
            self.ObjParse(obj_file)

    def ObjInfo(self):
        print("Num vertices  :    %d" % (len(self.nodes)))
        print("Num faces     :    %d" % (len(self.faces)))
        nmin, nmax = self.MinMaxNodes()
        print("Min/Max       :    %s %s" % (np.around(nmin, 3), np.around(nmax, 3)))

    @staticmethod
    def MinMax3d(arr):
        nmin = 1e9 * np.ones((3))
        nmax = -1e9 * np.ones((3))
        for a in arr:
            for i in range(3):
                nmin[i] = min(nmin[i], a[i])
                nmax[i] = max(nmax[i], a[i])
        return (nmin, nmax)

    def MinMaxNodes(self):
        return ObjFile.MinMax3d(self.nodes)

    def ObjParse(self, obj_file):
        f = open(obj_file)
        lines = f.readlines()
        f.close()
        nodes = []
        # add zero entry to get ids right
        nodes.append([0.0, 0.0, 0.0])
        faces = []
        for line in lines:
            if "v" == line[0] and line[1].isspace():  # do not match "vt" or "vn"
                v = line.split()
                nodes.append(ObjFile.ToFloats(v[1:])[:3])
            if "f" == line[0]:
                # remove /int
                line = re.sub(RE, "", line)
                f = line.split()
                faces.append(ObjFile.ToInts([s.split("/")[0] for s in f[1:]]))

        self.nodes = np.array(nodes)
        assert np.shape(self.nodes)[1] == 3
        self.faces = faces

    def ObjWrite(self, obj_file):
        f = open(obj_file, "w")
        for n in self.nodes[1:]:  # skip first dummy 'node'
            f.write("v ")
            for nn in n:
                f.write("%g " % (nn))
            f.write("\n")
        for ff in self.faces:
            f.write("f ")
            for fff in ff:
                f.write("%d " % (fff))
            f.write("\n")

    @staticmethod
    def ToFloats(n):
        if isinstance(n, list):
            v = []
            for nn in n:
                v.append(float(nn))
            return v
        else:
            return float(n)

    @staticmethod
    def ToInts(n):
        if isinstance(n, list):
            v = []
            for nn in n:
                v.append(int(nn))
            return v
        else:
            return int(n)

    @staticmethod
    def Normalize(v):
        v2 = np.linalg.norm(v)
        if v2 < 0.000000001:
            return v
        else:
            return v / v2

    def QuadToTria(self):
        trifaces = []
        for f in self.faces:
            if len(f) == 3:
                trifaces.append(f)
            elif len(f) == 4:
                f1 = [f[0], f[1], f[2]]
                f2 = [f[0], f[2], f[3]]
                trifaces.append(f1)
                trifaces.append(f2)
        return trifaces

    @staticmethod
    def ScaleVal(v, scale, minval=True):

        if minval:
            if v > 0:
                return v * (1.0 - scale)
            else:
                return v * scale
        else:  # maxval
            if v > 0:
                return v * scale
            else:
                return v * (1.0 - scale)

    def Plot(
        self,
        output_file=None,
        elevation=None,
        azim=None,
        width=None,
        height=None,
        scale=None,
        animate=None,
        obj_color = (0.5,0.5,0.5),
    ):
        plt.ioff()
        tri = self.QuadToTria()
        fig = plt.figure()
        # ax = fig.gca(projection='3d')
        ax = fig.add_subplot(111, projection="3d")
        ax.plot_trisurf(
            self.nodes[:, 0], self.nodes[:, 1], self.nodes[:, 2], triangles=tri, color = obj_color
        )
        ax.axis("off")
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        # enforce aspect ratio to avoid streching, see Issue https://github.com/pclausen/obj2png/issues/7
        limits = np.array([getattr(ax, f"get_{axis}lim")() for axis in "xyz"])
        ax.set_box_aspect(np.ptp(limits, axis=1))

        nmin, nmax = self.MinMaxNodes()
        if scale is not None:
            ax.set_xlim(
                ObjFile.ScaleVal(nmin[0], scale),
                ObjFile.ScaleVal(nmax[0], scale, False),
            )
            ax.set_ylim(
                ObjFile.ScaleVal(nmin[1], scale),
                ObjFile.ScaleVal(nmax[1], scale, False),
            )
            ax.set_zlim(
                ObjFile.ScaleVal(nmin[2], scale),
                ObjFile.ScaleVal(nmax[2], scale, False),
            )
        if elevation is not None and azim is not None:
            ax.view_init(elevation, azim)
        elif elevation is not None:
            ax.view_init(elevation, 30)
        elif azim is not None:
            ax.view_init(30, azim)
        else:
            ax.view_init(30, 30)

        if output_file:
            # fig.tight_layout()
            # fig.subplots_adjust(left=-0.2, bottom=-0.2, right = 1.2, top = 1.2,
            #    wspace = 0, hspace = 0)
            # ax.autoscale_view(tight = True)
            # ax.autoscale(tight = True)
            # ax.margins(tight = True)

            dpi = None
            if width and height:
                width_inches = 1.0 if width >= height else (width / height)
                height_inches = 1.0 if height >= width else (height / width)
                dpi = max(width, height)
                fig.set_size_inches(width_inches, height_inches)

            if output_file == "io":
                img_buf = io.BytesIO()
                plt.savefig(img_buf, dpi=dpi, transparent=True, format="png")
                plt.close()
                return Image.open(img_buf)
            plt.savefig(output_file, dpi=dpi, transparent=True)
            plt.close()
        else:
            if animate:
                # rotate the axes and update
                for elevation in np.linspace(-180, 180, 10):
                    for azim in np.linspace(-180, 180, 10):
                        print("--elevation {} --azim {}".format(elevation, azim))
                        ax.view_init(elevation, azim)
                        textvar = ax.text2D(
                            0.05,
                            0.95,
                            "--elevation {} --azim {}".format(elevation, azim),
                            transform=ax.transAxes,
                        )
                        plt.draw()
                        # plt.show()
                        plt.pause(0.5)
                        textvar.remove()
            else:
                plt.show()
class View3DGenerator(object):

    def __init__(self, obj_base_path, max_azim=360, min_azim=0, max_elev=60, min_elev=-60, padding = 100):
        self.base_path = obj_base_path
        self.min_azim = min_azim
        self.max_azim = max_azim
        self.min_elev = min_elev
        self.max_elev = max_elev
        self.padding = padding

    def __iter__(self):
        return self

    def __next__(self):
        '''
        Calls the .next() function. Does not support exact font sizes.
        '''
        return self.next()

    def next(self):
        obj_path = self.base_path
        while ".obj" not in obj_path:
            obj_path = os.path.join(obj_path, random.choice(os.listdir(obj_path)))
        ob = ObjFile(obj_path)
        # random parameters
        azim = random.choice(range(self.min_azim, self.max_azim)) # rotation around object
        elevation = random.choice(range(self.min_elev,self.max_elev)) # elevation of the camera
        l = random.gauss(0.6, 0.2)%1 # lightness
        img = ob.Plot(  output_file="io",
                        elevation=elevation,
                        azim=azim,
                        width=2000,
                        height=2000,
                        scale=None,
                        animate=None,
                        obj_color = (l,l,l))
        # convert to grayscale
        img = ImageOps.grayscale(img)
        # crop to content
        bb = getbb(img, threshold=240, pad = self.padding)
        img = img.crop(bb)
        return img